
/tmp/tt-disasm-fw_ncrisc-rj8wnd_0/out.elf:     file format elf32-littleriscv


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
    5474:	4680006f          	j	58dc <exit>

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
    54a8:	01a12023          	sw	s10,0(sp)
    54ac:	00200313          	li	t1,2
    54b0:	7c032073          	csrs	0x7c0,t1
    54b4:	00100313          	li	t1,1
    54b8:	01231313          	slli	t1,t1,0x12
    54bc:	0ff0000f          	fence
    54c0:	7c032073          	csrs	0x7c0,t1
    54c4:	00200313          	li	t1,2
    54c8:	7c033073          	csrc	0x7c0,t1
    54cc:	0ff0000f          	fence
    54d0:	0ff0000f          	fence
    54d4:	00800313          	li	t1,8
    54d8:	7c032073          	csrs	0x7c0,t1
    54dc:	2e4000ef          	jal	57c0 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0>
    54e0:	354000ef          	jal	5834 <_Z19noc_bank_table_inity.constprop.0>
    54e4:	3bc000ef          	jal	58a0 <_Z38noc_worker_logical_to_virtual_map_inity.constprop.0>
    54e8:	180000ef          	jal	5668 <_Z9risc_initv>
    54ec:	000017b7          	lui	a5,0x1
    54f0:	9a07c703          	lbu	a4,-1632(a5) # 9a0 <_start-0x4aa0>
    54f4:	06078793          	addi	a5,a5,96
    54f8:	ffb01cb7          	lui	s9,0xffb01
    54fc:	06000a93          	li	s5,96
    5500:	044c8c93          	addi	s9,s9,68 # ffb01044 <__fw_export_ldm_end+0x7d4>
    5504:	85418913          	addi	s2,gp,-1964 # ffb00044 <cb_interface>
    5508:	84e184a3          	sb	a4,-1975(gp) # ffb00039 <my_logical_x_>
    550c:	9417c783          	lbu	a5,-1727(a5)
    5510:	84f18423          	sb	a5,-1976(gp) # ffb00038 <my_logical_y_>
    5514:	8101a483          	lw	s1,-2032(gp) # ffb00000 <_ZL10ncrisc_run>
    5518:	00048023          	sb	zero,0(s1)
    551c:	0004c783          	lbu	a5,0(s1)
    5520:	0ff7f713          	zext.b	a4,a5
    5524:	fff78793          	addi	a5,a5,-1
    5528:	00078a63          	beqz	a5,553c <main+0xc4>
    552c:	f8070793          	addi	a5,a4,-128
    5530:	00078663          	beqz	a5,553c <main+0xc4>
    5534:	0ff0000f          	fence
    5538:	fe5ff06f          	j	551c <main+0xa4>
    553c:	06c02403          	lw	s0,108(zero) # 6c <_start-0x53d4>
    5540:	06c02783          	lw	a5,108(zero) # 6c <_start-0x53d4>
    5544:	00090593          	mv	a1,s2
    5548:	03540433          	mul	s0,s0,s5
    554c:	035787b3          	mul	a5,a5,s5
    5550:	07040413          	addi	s0,s0,112
    5554:	0707ac03          	lw	s8,112(a5)
    5558:	07c7d703          	lhu	a4,124(a5)
    555c:	0747a683          	lw	a3,116(a5)
    5560:	06078793          	addi	a5,a5,96
    5564:	01870733          	add	a4,a4,s8
    5568:	80ecac23          	sw	a4,-2024(s9)
    556c:	01e7d703          	lhu	a4,30(a5)
    5570:	00d70733          	add	a4,a4,a3
    5574:	80ecae23          	sw	a4,-2020(s9)
    5578:	0187a683          	lw	a3,24(a5)
    557c:	0207d703          	lhu	a4,32(a5)
    5580:	00d70733          	add	a4,a4,a3
    5584:	82eca023          	sw	a4,-2016(s9)
    5588:	02a7d703          	lhu	a4,42(a5)
    558c:	02c7d783          	lhu	a5,44(a5)
    5590:	03042d03          	lw	s10,48(s0)
    5594:	01870733          	add	a4,a4,s8
    5598:	018787b3          	add	a5,a5,s8
    559c:	84f1a023          	sw	a5,-1984(gp) # ffb00030 <crta_l1_base>
    55a0:	01245783          	lhu	a5,18(s0)
    55a4:	84e1a223          	sw	a4,-1980(gp) # ffb00034 <rta_l1_base>
    55a8:	018787b3          	add	a5,a5,s8
    55ac:	04042703          	lw	a4,64(s0)
    55b0:	0580006f          	j	5608 <.NO_CB360+0xc>
    55b4:	0047a683          	lw	a3,4(a5)
    55b8:	0007a603          	lw	a2,0(a5)
    55bc:	0087a803          	lw	a6,8(a5)
    55c0:	00c7a883          	lw	a7,12(a5)
    55c4:	00175713          	srli	a4,a4,0x1
    55c8:	00177293          	andi	t0,a4,1
    55cc:	0005ac23          	sw	zero,24(a1)
    55d0:	01078793          	addi	a5,a5,16
    55d4:	00d5a023          	sw	a3,0(a1)
    55d8:	00d606b3          	add	a3,a2,a3
    55dc:	00d5a223          	sw	a3,4(a1)
    55e0:	00c5aa23          	sw	a2,20(a1)
    55e4:	0105a623          	sw	a6,12(a1)
    55e8:	00c5a823          	sw	a2,16(a1)
    55ec:	0115a423          	sw	a7,8(a1)
    55f0:	02058593          	addi	a1,a1,32
    55f4:	fc0290e3          	bnez	t0,55b4 <main+0x13c>
    55f8:	00070e63          	beqz	a4,5614 <.NO_CB360+0x18>

000055fc <.NO_CB360>:
    55fc:	01078793          	addi	a5,a5,16
    5600:	02058593          	addi	a1,a1,32
    5604:	00175713          	srli	a4,a4,0x1
    5608:	00177293          	andi	t0,a4,1
    560c:	fa0294e3          	bnez	t0,55b4 <main+0x13c>
    5610:	fe0716e3          	bnez	a4,55fc <.NO_CB360>
    5614:	01445503          	lhu	a0,20(s0)
    5618:	04644583          	lbu	a1,70(s0)
    561c:	01850533          	add	a0,a0,s8
    5620:	08c000ef          	jal	56ac <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>
    5624:	05c44703          	lbu	a4,92(s0)
    5628:	8491c783          	lbu	a5,-1975(gp) # ffb00039 <my_logical_x_>
    562c:	40e787b3          	sub	a5,a5,a4
    5630:	82f18ea3          	sb	a5,-1987(gp) # ffb0002d <my_relative_x_>
    5634:	05d44703          	lbu	a4,93(s0)
    5638:	8481c783          	lbu	a5,-1976(gp) # ffb00038 <my_logical_y_>
    563c:	40e787b3          	sub	a5,a5,a4
    5640:	82f18e23          	sb	a5,-1988(gp) # ffb0002c <my_relative_y_>
    5644:	08000793          	li	a5,128
    5648:	0004c703          	lbu	a4,0(s1)
    564c:	00f71a63          	bne	a4,a5,5660 <.NO_CB360+0x64>
    5650:	018d0d33          	add	s10,s10,s8
    5654:	000d00e7          	jalr	s10
    5658:	00048023          	sb	zero,0(s1)
    565c:	ec1ff06f          	j	551c <main+0xa4>
    5660:	0ff0000f          	fence
    5664:	fe5ff06f          	j	5648 <.NO_CB360+0x4c>

00005668 <_Z9risc_initv>:
    5668:	ffb207b7          	lui	a5,0xffb20
    566c:	1487a783          	lw	a5,328(a5) # ffb20148 <__stack_top+0x1e148>
    5670:	03f7f713          	andi	a4,a5,63
    5674:	0067d793          	srli	a5,a5,0x6
    5678:	84e18823          	sb	a4,-1968(gp) # ffb00040 <my_x>
    567c:	03f7f793          	andi	a5,a5,63
    5680:	84f18623          	sb	a5,-1972(gp) # ffb0003c <my_y>
    5684:	ffb307b7          	lui	a5,0xffb30
    5688:	1487a783          	lw	a5,328(a5) # ffb30148 <__stack_top+0x2e148>
    568c:	85018693          	addi	a3,gp,-1968 # ffb00040 <my_x>
    5690:	03f7f613          	andi	a2,a5,63
    5694:	0067d793          	srli	a5,a5,0x6
    5698:	84c18713          	addi	a4,gp,-1972 # ffb0003c <my_y>
    569c:	03f7f793          	andi	a5,a5,63
    56a0:	00c680a3          	sb	a2,1(a3)
    56a4:	00f700a3          	sb	a5,1(a4)
    56a8:	00008067          	ret

000056ac <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>:
    56ac:	fff58593          	addi	a1,a1,-1
    56b0:	85418793          	addi	a5,gp,-1964 # ffb00044 <cb_interface>
    56b4:	01f00313          	li	t1,31
    56b8:	00659463          	bne	a1,t1,56c0 <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x14>
    56bc:	00008067          	ret
    56c0:	00052683          	lw	a3,0(a0)
    56c4:	00452803          	lw	a6,4(a0)
    56c8:	0006af83          	lw	t6,0(a3)
    56cc:	0046af03          	lw	t5,4(a3)
    56d0:	0086a603          	lw	a2,8(a3)
    56d4:	00c6a703          	lw	a4,12(a3)
    56d8:	0106ae03          	lw	t3,16(a3)
    56dc:	0146ae83          	lw	t4,20(a3)
    56e0:	0186a883          	lw	a7,24(a3)
    56e4:	fff80713          	addi	a4,a6,-1
    56e8:	01c70733          	add	a4,a4,t3
    56ec:	40c70733          	sub	a4,a4,a2
    56f0:	03075733          	divu	a4,a4,a6
    56f4:	03070733          	mul	a4,a4,a6
    56f8:	00c70733          	add	a4,a4,a2
    56fc:	040f8863          	beqz	t6,574c <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0xa0>
    5700:	3ed7a023          	sw	a3,992(a5)
    5704:	3ec7a223          	sw	a2,996(a5)
    5708:	3fc7a823          	sw	t3,1008(a5)
    570c:	3fd7aa23          	sw	t4,1012(a5)
    5710:	3f17ac23          	sw	a7,1016(a5)
    5714:	3fe7ae23          	sw	t5,1020(a5)
    5718:	00c6a883          	lw	a7,12(a3)
    571c:	011606b3          	add	a3,a2,a7
    5720:	0308f8b3          	remu	a7,a7,a6
    5724:	411686b3          	sub	a3,a3,a7
    5728:	00d77463          	bgeu	a4,a3,5730 <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x84>
    572c:	00070613          	mv	a2,a4
    5730:	3ec7a823          	sw	a2,1008(a5)
    5734:	3ed7a423          	sw	a3,1000(a5)
    5738:	3f07a623          	sw	a6,1004(a5)
    573c:	00850513          	addi	a0,a0,8
    5740:	fff30313          	addi	t1,t1,-1
    5744:	fe078793          	addi	a5,a5,-32
    5748:	f71ff06f          	j	56b8 <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0xc>
    574c:	000eaf03          	lw	t5,0(t4)
    5750:	004eae83          	lw	t4,4(t4)
    5754:	01088893          	addi	a7,a7,16
    5758:	3ed7a023          	sw	a3,992(a5)
    575c:	3ec7a223          	sw	a2,996(a5)
    5760:	3fc7a823          	sw	t3,1008(a5)
    5764:	3f17ae23          	sw	a7,1020(a5)
    5768:	3fe7aa23          	sw	t5,1012(a5)
    576c:	3fd7ac23          	sw	t4,1016(a5)
    5770:	fa9ff06f          	j	5718 <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x6c>

00005774 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>:
    5774:	00200793          	li	a5,2
    5778:	02c7c063          	blt	a5,a2,5798 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x24>
    577c:	00c05c63          	blez	a2,5794 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    5780:	0005a703          	lw	a4,0(a1)
    5784:	00e52023          	sw	a4,0(a0)
    5788:	00f61663          	bne	a2,a5,5794 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    578c:	0045a783          	lw	a5,4(a1)
    5790:	00f52223          	sw	a5,4(a0)
    5794:	00008067          	ret
    5798:	0005a803          	lw	a6,0(a1)
    579c:	0045a683          	lw	a3,4(a1)
    57a0:	0085a703          	lw	a4,8(a1)
    57a4:	00c58593          	addi	a1,a1,12
    57a8:	00c50513          	addi	a0,a0,12
    57ac:	ffd60613          	addi	a2,a2,-3
    57b0:	ff052a23          	sw	a6,-12(a0)
    57b4:	fed52c23          	sw	a3,-8(a0)
    57b8:	fee52e23          	sw	a4,-4(a0)
    57bc:	fbdff06f          	j	5778 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x4>

000057c0 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0>:
    57c0:	ffb007b7          	lui	a5,0xffb00
    57c4:	ffb01737          	lui	a4,0xffb01
    57c8:	01478793          	addi	a5,a5,20 # ffb00014 <noc_nonposted_writes_acked>
    57cc:	86870713          	addi	a4,a4,-1944 # ffb00868 <__ldm_bss_end>
    57d0:	04f77463          	bgeu	a4,a5,5818 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x58>
    57d4:	ff878693          	addi	a3,a5,-8
    57d8:	00d76863          	bltu	a4,a3,57e8 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x28>
    57dc:	fe07aa23          	sw	zero,-12(a5)
    57e0:	fe07a823          	sw	zero,-16(a5)
    57e4:	00078693          	mv	a3,a5
    57e8:	ffc68793          	addi	a5,a3,-4
    57ec:	00f76463          	bltu	a4,a5,57f4 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x34>
    57f0:	fe06ac23          	sw	zero,-8(a3)
    57f4:	0000a5b7          	lui	a1,0xa
    57f8:	81018513          	addi	a0,gp,-2032 # ffb00000 <_ZL10ncrisc_run>
    57fc:	6b058593          	addi	a1,a1,1712 # a6b0 <__fw_export_text_end+0x4dd0>
    5800:	02b50863          	beq	a0,a1,5830 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x70>
    5804:	ffb00637          	lui	a2,0xffb00
    5808:	00460613          	addi	a2,a2,4 # ffb00004 <noc_reads_num_issued>
    580c:	40a60633          	sub	a2,a2,a0
    5810:	40265613          	srai	a2,a2,0x2
    5814:	f61ff06f          	j	5774 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5818:	fe07ae23          	sw	zero,-4(a5)
    581c:	fe07ac23          	sw	zero,-8(a5)
    5820:	fe07aa23          	sw	zero,-12(a5)
    5824:	fe07a823          	sw	zero,-16(a5)
    5828:	01078793          	addi	a5,a5,16
    582c:	fa5ff06f          	j	57d0 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x10>
    5830:	00008067          	ret

00005834 <_Z19noc_bank_table_inity.constprop.0>:
    5834:	ff010113          	addi	sp,sp,-16
    5838:	00812423          	sw	s0,8(sp)
    583c:	00912223          	sw	s1,4(sp)
    5840:	85418413          	addi	s0,gp,-1964 # ffb00044 <cb_interface>
    5844:	000114b7          	lui	s1,0x11
    5848:	6b048593          	addi	a1,s1,1712 # 116b0 <__fw_export_text_end+0xbdd0>
    584c:	40040513          	addi	a0,s0,1024
    5850:	00700613          	li	a2,7
    5854:	00112623          	sw	ra,12(sp)
    5858:	f1dff0ef          	jal	5774 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    585c:	6cc48593          	addi	a1,s1,1740
    5860:	41c40513          	addi	a0,s0,1052
    5864:	07800613          	li	a2,120
    5868:	f0dff0ef          	jal	5774 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    586c:	000124b7          	lui	s1,0x12
    5870:	8ac48593          	addi	a1,s1,-1876 # 118ac <__fw_export_text_end+0xbfcc>
    5874:	5fc40513          	addi	a0,s0,1532
    5878:	00700613          	li	a2,7
    587c:	ef9ff0ef          	jal	5774 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5880:	61840513          	addi	a0,s0,1560
    5884:	00812403          	lw	s0,8(sp)
    5888:	00c12083          	lw	ra,12(sp)
    588c:	8c848593          	addi	a1,s1,-1848
    5890:	00412483          	lw	s1,4(sp)
    5894:	07800613          	li	a2,120
    5898:	01010113          	addi	sp,sp,16
    589c:	ed9ff06f          	j	5774 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>

000058a0 <_Z38noc_worker_logical_to_virtual_map_inity.constprop.0>:
    58a0:	ff010113          	addi	sp,sp,-16
    58a4:	00812423          	sw	s0,8(sp)
    58a8:	00012437          	lui	s0,0x12
    58ac:	eb040593          	addi	a1,s0,-336 # 11eb0 <__fw_export_text_end+0xc5d0>
    58b0:	00500613          	li	a2,5
    58b4:	04c18513          	addi	a0,gp,76 # ffb0083c <worker_logical_col_to_virtual_col>
    58b8:	00112623          	sw	ra,12(sp)
    58bc:	eb9ff0ef          	jal	5774 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    58c0:	ec440593          	addi	a1,s0,-316
    58c4:	00812403          	lw	s0,8(sp)
    58c8:	00c12083          	lw	ra,12(sp)
    58cc:	00300613          	li	a2,3
    58d0:	06018513          	addi	a0,gp,96 # ffb00850 <worker_logical_row_to_virtual_row>
    58d4:	01010113          	addi	sp,sp,16
    58d8:	e9dff06f          	j	5774 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>

000058dc <exit>:
    58dc:	0000006f          	j	58dc <exit>
