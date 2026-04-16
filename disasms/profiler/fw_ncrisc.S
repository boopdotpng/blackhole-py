
/tmp/tt-disasm-fw_ncrisc-besb5kmh/out.elf:     file format elf32-littleriscv


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
    5474:	5d80006f          	j	5a4c <exit>

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
    54d8:	000014b7          	lui	s1,0x1
    54dc:	454000ef          	jal	5930 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0>
    54e0:	4c4000ef          	jal	59a4 <_Z19noc_bank_table_inity.constprop.0>
    54e4:	52c000ef          	jal	5a10 <_Z38noc_worker_logical_to_virtual_map_inity.constprop.0>
    54e8:	1e0000ef          	jal	56c8 <_Z9risc_initv>
    54ec:	9a04c703          	lbu	a4,-1632(s1) # 9a0 <_start-0x4aa0>
    54f0:	fff48a93          	addi	s5,s1,-1
    54f4:	ffb12937          	lui	s2,0xffb12
    54f8:	80000a37          	lui	s4,0x80000
    54fc:	84e184a3          	sb	a4,-1975(gp) # ffb00039 <my_logical_x_>
    5500:	9a14c783          	lbu	a5,-1631(s1)
    5504:	7ff48493          	addi	s1,s1,2047
    5508:	24148493          	addi	s1,s1,577
    550c:	84f18423          	sb	a5,-1976(gp) # ffb00038 <my_logical_y_>
    5510:	8101a983          	lw	s3,-2032(gp) # ffb00000 <_ZL10ncrisc_run>
    5514:	00098023          	sb	zero,0(s3)
    5518:	0009c783          	lbu	a5,0(s3)
    551c:	0ff7f713          	zext.b	a4,a5
    5520:	fff78793          	addi	a5,a5,-1
    5524:	00078a63          	beqz	a5,5538 <main+0xc0>
    5528:	f8070793          	addi	a5,a4,-128
    552c:	00078663          	beqz	a5,5538 <main+0xc0>
    5530:	0ff0000f          	fence
    5534:	fe5ff06f          	j	5518 <main+0xa0>
    5538:	1d4000ef          	jal	570c <_ZN15kernel_profiler13init_profilerEttt.constprop.0>
    553c:	00000513          	li	a0,0
    5540:	1f4000ef          	jal	5734 <_ZN15kernel_profiler12get_const_idEmNS_11PacketTypesE.constprop.0>
    5544:	00c51513          	slli	a0,a0,0xc
    5548:	1f492783          	lw	a5,500(s2) # ffb121f4 <__stack_top+0x101f4>
    554c:	06000713          	li	a4,96
    5550:	86c18593          	addi	a1,gp,-1940 # ffb0005c <cb_interface>
    5554:	0157f7b3          	and	a5,a5,s5
    5558:	00f56533          	or	a0,a0,a5
    555c:	01456533          	or	a0,a0,s4
    5560:	80a4a823          	sw	a0,-2032(s1)
    5564:	1f092783          	lw	a5,496(s2)
    5568:	80f4aa23          	sw	a5,-2028(s1)
    556c:	06c02403          	lw	s0,108(zero) # 6c <_start-0x53d4>
    5570:	06c02783          	lw	a5,108(zero) # 6c <_start-0x53d4>
    5574:	02e40433          	mul	s0,s0,a4
    5578:	02e787b3          	mul	a5,a5,a4
    557c:	07040413          	addi	s0,s0,112
    5580:	00e787b3          	add	a5,a5,a4
    5584:	0107ac03          	lw	s8,16(a5)
    5588:	01c7d683          	lhu	a3,28(a5)
    558c:	ffb01737          	lui	a4,0xffb01
    5590:	05c70713          	addi	a4,a4,92 # ffb0105c <__fw_export_ldm_end+0x7dc>
    5594:	0147a603          	lw	a2,20(a5)
    5598:	018686b3          	add	a3,a3,s8
    559c:	80d72c23          	sw	a3,-2024(a4)
    55a0:	01e7d683          	lhu	a3,30(a5)
    55a4:	00c686b3          	add	a3,a3,a2
    55a8:	80d72e23          	sw	a3,-2020(a4)
    55ac:	0187a603          	lw	a2,24(a5)
    55b0:	0207d683          	lhu	a3,32(a5)
    55b4:	00c686b3          	add	a3,a3,a2
    55b8:	82d72023          	sw	a3,-2016(a4)
    55bc:	02a7d703          	lhu	a4,42(a5)
    55c0:	02c7d783          	lhu	a5,44(a5)
    55c4:	03042c83          	lw	s9,48(s0)
    55c8:	01870733          	add	a4,a4,s8
    55cc:	018787b3          	add	a5,a5,s8
    55d0:	84e1a223          	sw	a4,-1980(gp) # ffb00034 <rta_l1_base>
    55d4:	84f1a023          	sw	a5,-1984(gp) # ffb00030 <crta_l1_base>
    55d8:	01245783          	lhu	a5,18(s0)
    55dc:	04042703          	lw	a4,64(s0)
    55e0:	018787b3          	add	a5,a5,s8
    55e4:	0580006f          	j	563c <.NO_CB501+0xc>
    55e8:	0047a683          	lw	a3,4(a5)
    55ec:	0007a603          	lw	a2,0(a5)
    55f0:	0087a803          	lw	a6,8(a5)
    55f4:	00c7a883          	lw	a7,12(a5)
    55f8:	00175713          	srli	a4,a4,0x1
    55fc:	00177293          	andi	t0,a4,1
    5600:	0005ac23          	sw	zero,24(a1)
    5604:	01078793          	addi	a5,a5,16
    5608:	00d5a023          	sw	a3,0(a1)
    560c:	00d606b3          	add	a3,a2,a3
    5610:	00d5a223          	sw	a3,4(a1)
    5614:	00c5aa23          	sw	a2,20(a1)
    5618:	0105a623          	sw	a6,12(a1)
    561c:	00c5a823          	sw	a2,16(a1)
    5620:	0115a423          	sw	a7,8(a1)
    5624:	02058593          	addi	a1,a1,32
    5628:	fc0290e3          	bnez	t0,55e8 <main+0x170>
    562c:	00070e63          	beqz	a4,5648 <.NO_CB501+0x18>

00005630 <.NO_CB501>:
    5630:	01078793          	addi	a5,a5,16
    5634:	02058593          	addi	a1,a1,32
    5638:	00175713          	srli	a4,a4,0x1
    563c:	00177293          	andi	t0,a4,1
    5640:	fa0294e3          	bnez	t0,55e8 <main+0x170>
    5644:	fe0716e3          	bnez	a4,5630 <.NO_CB501>
    5648:	01445503          	lhu	a0,20(s0)
    564c:	04644583          	lbu	a1,70(s0)
    5650:	01850533          	add	a0,a0,s8
    5654:	1c8000ef          	jal	581c <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>
    5658:	05c44703          	lbu	a4,92(s0)
    565c:	8491c783          	lbu	a5,-1975(gp) # ffb00039 <my_logical_x_>
    5660:	40e787b3          	sub	a5,a5,a4
    5664:	82f18ea3          	sb	a5,-1987(gp) # ffb0002d <my_relative_x_>
    5668:	05d44703          	lbu	a4,93(s0)
    566c:	8481c783          	lbu	a5,-1976(gp) # ffb00038 <my_logical_y_>
    5670:	40e787b3          	sub	a5,a5,a4
    5674:	82f18e23          	sb	a5,-1988(gp) # ffb0002c <my_relative_y_>
    5678:	08000793          	li	a5,128
    567c:	0009c703          	lbu	a4,0(s3)
    5680:	04f71063          	bne	a4,a5,56c0 <.NO_CB501+0x90>
    5684:	018c8cb3          	add	s9,s9,s8
    5688:	000c80e7          	jalr	s9
    568c:	00098023          	sb	zero,0(s3)
    5690:	00100513          	li	a0,1
    5694:	0a0000ef          	jal	5734 <_ZN15kernel_profiler12get_const_idEmNS_11PacketTypesE.constprop.0>
    5698:	00c51513          	slli	a0,a0,0xc
    569c:	1f492783          	lw	a5,500(s2)
    56a0:	0157f7b3          	and	a5,a5,s5
    56a4:	00f56533          	or	a0,a0,a5
    56a8:	01456533          	or	a0,a0,s4
    56ac:	80a4ac23          	sw	a0,-2024(s1)
    56b0:	1f092783          	lw	a5,496(s2)
    56b4:	80f4ae23          	sw	a5,-2020(s1)
    56b8:	090000ef          	jal	5748 <_ZN15kernel_profiler15finish_profilerEv>
    56bc:	e5dff06f          	j	5518 <main+0xa0>
    56c0:	0ff0000f          	fence
    56c4:	fb9ff06f          	j	567c <.NO_CB501+0x4c>

000056c8 <_Z9risc_initv>:
    56c8:	ffb207b7          	lui	a5,0xffb20
    56cc:	1487a783          	lw	a5,328(a5) # ffb20148 <__stack_top+0x1e148>
    56d0:	03f7f713          	andi	a4,a5,63
    56d4:	0067d793          	srli	a5,a5,0x6
    56d8:	86e18423          	sb	a4,-1944(gp) # ffb00058 <my_x>
    56dc:	03f7f793          	andi	a5,a5,63
    56e0:	86f18223          	sb	a5,-1948(gp) # ffb00054 <my_y>
    56e4:	ffb307b7          	lui	a5,0xffb30
    56e8:	1487a783          	lw	a5,328(a5) # ffb30148 <__stack_top+0x2e148>
    56ec:	86818693          	addi	a3,gp,-1944 # ffb00058 <my_x>
    56f0:	03f7f613          	andi	a2,a5,63
    56f4:	0067d793          	srli	a5,a5,0x6
    56f8:	86418713          	addi	a4,gp,-1948 # ffb00054 <my_y>
    56fc:	03f7f793          	andi	a5,a5,63
    5700:	00c680a3          	sb	a2,1(a3)
    5704:	00f700a3          	sb	a5,1(a4)
    5708:	00008067          	ret

0000570c <_ZN15kernel_profiler13init_profilerEttt.constprop.0>:
    570c:	00c00713          	li	a4,12
    5710:	86e1a023          	sw	a4,-1952(gp) # ffb00050 <_ZN15kernel_profiler6wIndexE>
    5714:	8401ae23          	sw	zero,-1956(gp) # ffb0004c <_ZN15kernel_profiler9stackSizeE>
    5718:	85418713          	addi	a4,gp,-1964 # ffb00044 <_ZN15kernel_profiler6sumIDsE>
    571c:	84c18793          	addi	a5,gp,-1972 # ffb0003c <_ZN15kernel_profiler4sumsE>
    5720:	00072023          	sw	zero,0(a4)
    5724:	0007a023          	sw	zero,0(a5)
    5728:	00072223          	sw	zero,4(a4)
    572c:	0007a223          	sw	zero,4(a5)
    5730:	00008067          	ret

00005734 <_ZN15kernel_profiler12get_const_idEmNS_11PacketTypesE.constprop.0>:
    5734:	000037b7          	lui	a5,0x3
    5738:	d7178793          	addi	a5,a5,-655 # 2d71 <_start-0x26cf>
    573c:	01051513          	slli	a0,a0,0x10
    5740:	00f56533          	or	a0,a0,a5
    5744:	00008067          	ret

00005748 <_ZN15kernel_profiler15finish_profilerEv>:
    5748:	8601a783          	lw	a5,-1952(gp) # ffb00050 <_ZN15kernel_profiler6wIndexE>
    574c:	00078693          	mv	a3,a5
    5750:	00000593          	li	a1,0
    5754:	00000713          	li	a4,0
    5758:	84c18813          	addi	a6,gp,-1972 # ffb0003c <_ZN15kernel_profiler4sumsE>
    575c:	1ff00e93          	li	t4,511
    5760:	00400e13          	li	t3,4
    5764:	01058633          	add	a2,a1,a6
    5768:	00062883          	lw	a7,0(a2)
    576c:	04088463          	beqz	a7,57b4 <_ZN15kernel_profiler15finish_profilerEv+0x6c>
    5770:	04dee263          	bltu	t4,a3,57b4 <_ZN15kernel_profiler15finish_profilerEv+0x6c>
    5774:	85418713          	addi	a4,gp,-1964 # ffb00044 <_ZN15kernel_profiler6sumIDsE>
    5778:	00e58733          	add	a4,a1,a4
    577c:	00072703          	lw	a4,0(a4)
    5780:	0ffff637          	lui	a2,0xffff
    5784:	00c71713          	slli	a4,a4,0xc
    5788:	00c77733          	and	a4,a4,a2
    578c:	00001337          	lui	t1,0x1
    5790:	a0000637          	lui	a2,0xa0000
    5794:	00c76733          	or	a4,a4,a2
    5798:	a4030613          	addi	a2,t1,-1472 # a40 <_start-0x4a00>
    579c:	20c6c633          	sh2add	a2,a3,a2
    57a0:	00660633          	add	a2,a2,t1
    57a4:	80e62023          	sw	a4,-2048(a2) # 9ffff800 <__fw_export_text_end+0x9fff9db0>
    57a8:	81162223          	sw	a7,-2044(a2)
    57ac:	00268693          	addi	a3,a3,2
    57b0:	00100713          	li	a4,1
    57b4:	05c59063          	bne	a1,t3,57f4 <_ZN15kernel_profiler15finish_profilerEv+0xac>
    57b8:	00070663          	beqz	a4,57c4 <_ZN15kernel_profiler15finish_profilerEv+0x7c>
    57bc:	86d1a023          	sw	a3,-1952(gp) # ffb00050 <_ZN15kernel_profiler6wIndexE>
    57c0:	00068793          	mv	a5,a3
    57c4:	00000713          	li	a4,0
    57c8:	00000693          	li	a3,0
    57cc:	1ff00593          	li	a1,511
    57d0:	00001837          	lui	a6,0x1
    57d4:	800008b7          	lui	a7,0x80000
    57d8:	0037f613          	andi	a2,a5,3
    57dc:	02c6e063          	bltu	a3,a2,57fc <_ZN15kernel_profiler15finish_profilerEv+0xb4>
    57e0:	00070463          	beqz	a4,57e8 <_ZN15kernel_profiler15finish_profilerEv+0xa0>
    57e4:	86f1a023          	sw	a5,-1952(gp) # ffb00050 <_ZN15kernel_profiler6wIndexE>
    57e8:	00001737          	lui	a4,0x1
    57ec:	9cf72c23          	sw	a5,-1576(a4) # 9d8 <_start-0x4a68>
    57f0:	00008067          	ret
    57f4:	00400593          	li	a1,4
    57f8:	f6dff06f          	j	5764 <_ZN15kernel_profiler15finish_profilerEv+0x1c>
    57fc:	00f5ec63          	bltu	a1,a5,5814 <_ZN15kernel_profiler15finish_profilerEv+0xcc>
    5800:	2107c733          	sh2add	a4,a5,a6
    5804:	25172023          	sw	a7,576(a4)
    5808:	24072223          	sw	zero,580(a4)
    580c:	00278793          	addi	a5,a5,2
    5810:	00100713          	li	a4,1
    5814:	00168693          	addi	a3,a3,1
    5818:	fc1ff06f          	j	57d8 <_ZN15kernel_profiler15finish_profilerEv+0x90>

0000581c <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>:
    581c:	fff58593          	addi	a1,a1,-1
    5820:	86c18793          	addi	a5,gp,-1940 # ffb0005c <cb_interface>
    5824:	01f00313          	li	t1,31
    5828:	00659463          	bne	a1,t1,5830 <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x14>
    582c:	00008067          	ret
    5830:	00052683          	lw	a3,0(a0)
    5834:	00452803          	lw	a6,4(a0)
    5838:	0006af83          	lw	t6,0(a3)
    583c:	0046af03          	lw	t5,4(a3)
    5840:	0086a603          	lw	a2,8(a3)
    5844:	00c6a703          	lw	a4,12(a3)
    5848:	0106ae03          	lw	t3,16(a3)
    584c:	0146ae83          	lw	t4,20(a3)
    5850:	0186a883          	lw	a7,24(a3)
    5854:	fff80713          	addi	a4,a6,-1 # fff <_start-0x4441>
    5858:	01c70733          	add	a4,a4,t3
    585c:	40c70733          	sub	a4,a4,a2
    5860:	03075733          	divu	a4,a4,a6
    5864:	03070733          	mul	a4,a4,a6
    5868:	00c70733          	add	a4,a4,a2
    586c:	040f8863          	beqz	t6,58bc <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0xa0>
    5870:	3ed7a023          	sw	a3,992(a5)
    5874:	3ec7a223          	sw	a2,996(a5)
    5878:	3fc7a823          	sw	t3,1008(a5)
    587c:	3fd7aa23          	sw	t4,1012(a5)
    5880:	3f17ac23          	sw	a7,1016(a5)
    5884:	3fe7ae23          	sw	t5,1020(a5)
    5888:	00c6a883          	lw	a7,12(a3)
    588c:	011606b3          	add	a3,a2,a7
    5890:	0308f8b3          	remu	a7,a7,a6
    5894:	411686b3          	sub	a3,a3,a7
    5898:	00d77463          	bgeu	a4,a3,58a0 <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x84>
    589c:	00070613          	mv	a2,a4
    58a0:	3ec7a823          	sw	a2,1008(a5)
    58a4:	3ed7a423          	sw	a3,1000(a5)
    58a8:	3f07a623          	sw	a6,1004(a5)
    58ac:	00850513          	addi	a0,a0,8
    58b0:	fff30313          	addi	t1,t1,-1
    58b4:	fe078793          	addi	a5,a5,-32
    58b8:	f71ff06f          	j	5828 <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0xc>
    58bc:	000eaf03          	lw	t5,0(t4)
    58c0:	004eae83          	lw	t4,4(t4)
    58c4:	01088893          	addi	a7,a7,16 # 80000010 <__fw_export_text_end+0x7fffa5c0>
    58c8:	3ed7a023          	sw	a3,992(a5)
    58cc:	3ec7a223          	sw	a2,996(a5)
    58d0:	3fc7a823          	sw	t3,1008(a5)
    58d4:	3f17ae23          	sw	a7,1020(a5)
    58d8:	3fe7aa23          	sw	t5,1012(a5)
    58dc:	3fd7ac23          	sw	t4,1016(a5)
    58e0:	fa9ff06f          	j	5888 <_ZN12experimental26setup_remote_cb_interfacesILb0EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x6c>

000058e4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>:
    58e4:	00200793          	li	a5,2
    58e8:	02c7c063          	blt	a5,a2,5908 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x24>
    58ec:	00c05c63          	blez	a2,5904 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    58f0:	0005a703          	lw	a4,0(a1)
    58f4:	00e52023          	sw	a4,0(a0)
    58f8:	00f61663          	bne	a2,a5,5904 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    58fc:	0045a783          	lw	a5,4(a1)
    5900:	00f52223          	sw	a5,4(a0)
    5904:	00008067          	ret
    5908:	0005a803          	lw	a6,0(a1)
    590c:	0045a683          	lw	a3,4(a1)
    5910:	0085a703          	lw	a4,8(a1)
    5914:	00c58593          	addi	a1,a1,12
    5918:	00c50513          	addi	a0,a0,12
    591c:	ffd60613          	addi	a2,a2,-3
    5920:	ff052a23          	sw	a6,-12(a0)
    5924:	fed52c23          	sw	a3,-8(a0)
    5928:	fee52e23          	sw	a4,-4(a0)
    592c:	fbdff06f          	j	58e8 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x4>

00005930 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0>:
    5930:	ffb007b7          	lui	a5,0xffb00
    5934:	ffb01737          	lui	a4,0xffb01
    5938:	01478793          	addi	a5,a5,20 # ffb00014 <noc_nonposted_writes_acked>
    593c:	88070713          	addi	a4,a4,-1920 # ffb00880 <__fw_export_ldm_end>
    5940:	04f77463          	bgeu	a4,a5,5988 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x58>
    5944:	ff878693          	addi	a3,a5,-8
    5948:	00d76863          	bltu	a4,a3,5958 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x28>
    594c:	fe07aa23          	sw	zero,-12(a5)
    5950:	fe07a823          	sw	zero,-16(a5)
    5954:	00078693          	mv	a3,a5
    5958:	ffc68793          	addi	a5,a3,-4
    595c:	00f76463          	bltu	a4,a5,5964 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x34>
    5960:	fe06ac23          	sw	zero,-8(a3)
    5964:	0000a5b7          	lui	a1,0xa
    5968:	81018513          	addi	a0,gp,-2032 # ffb00000 <_ZL10ncrisc_run>
    596c:	6b058593          	addi	a1,a1,1712 # a6b0 <__fw_export_text_end+0x4c60>
    5970:	02b50863          	beq	a0,a1,59a0 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x70>
    5974:	ffb00637          	lui	a2,0xffb00
    5978:	00460613          	addi	a2,a2,4 # ffb00004 <noc_reads_num_issued>
    597c:	40a60633          	sub	a2,a2,a0
    5980:	40265613          	srai	a2,a2,0x2
    5984:	f61ff06f          	j	58e4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5988:	fe07ae23          	sw	zero,-4(a5)
    598c:	fe07ac23          	sw	zero,-8(a5)
    5990:	fe07aa23          	sw	zero,-12(a5)
    5994:	fe07a823          	sw	zero,-16(a5)
    5998:	01078793          	addi	a5,a5,16
    599c:	fa5ff06f          	j	5940 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x10>
    59a0:	00008067          	ret

000059a4 <_Z19noc_bank_table_inity.constprop.0>:
    59a4:	ff010113          	addi	sp,sp,-16
    59a8:	00812423          	sw	s0,8(sp)
    59ac:	00912223          	sw	s1,4(sp)
    59b0:	86c18413          	addi	s0,gp,-1940 # ffb0005c <cb_interface>
    59b4:	000114b7          	lui	s1,0x11
    59b8:	6b048593          	addi	a1,s1,1712 # 116b0 <__fw_export_text_end+0xbc60>
    59bc:	40040513          	addi	a0,s0,1024
    59c0:	00700613          	li	a2,7
    59c4:	00112623          	sw	ra,12(sp)
    59c8:	f1dff0ef          	jal	58e4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    59cc:	6cc48593          	addi	a1,s1,1740
    59d0:	41c40513          	addi	a0,s0,1052
    59d4:	07800613          	li	a2,120
    59d8:	f0dff0ef          	jal	58e4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    59dc:	000124b7          	lui	s1,0x12
    59e0:	8ac48593          	addi	a1,s1,-1876 # 118ac <__fw_export_text_end+0xbe5c>
    59e4:	5fc40513          	addi	a0,s0,1532
    59e8:	00700613          	li	a2,7
    59ec:	ef9ff0ef          	jal	58e4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    59f0:	61840513          	addi	a0,s0,1560
    59f4:	00812403          	lw	s0,8(sp)
    59f8:	00c12083          	lw	ra,12(sp)
    59fc:	8c848593          	addi	a1,s1,-1848
    5a00:	00412483          	lw	s1,4(sp)
    5a04:	07800613          	li	a2,120
    5a08:	01010113          	addi	sp,sp,16
    5a0c:	ed9ff06f          	j	58e4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>

00005a10 <_Z38noc_worker_logical_to_virtual_map_inity.constprop.0>:
    5a10:	ff010113          	addi	sp,sp,-16
    5a14:	00812423          	sw	s0,8(sp)
    5a18:	00012437          	lui	s0,0x12
    5a1c:	eb040593          	addi	a1,s0,-336 # 11eb0 <__fw_export_text_end+0xc460>
    5a20:	00500613          	li	a2,5
    5a24:	06418513          	addi	a0,gp,100 # ffb00854 <worker_logical_col_to_virtual_col>
    5a28:	00112623          	sw	ra,12(sp)
    5a2c:	eb9ff0ef          	jal	58e4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5a30:	ec440593          	addi	a1,s0,-316
    5a34:	00812403          	lw	s0,8(sp)
    5a38:	00c12083          	lw	ra,12(sp)
    5a3c:	00300613          	li	a2,3
    5a40:	07818513          	addi	a0,gp,120 # ffb00868 <worker_logical_row_to_virtual_row>
    5a44:	01010113          	addi	sp,sp,16
    5a48:	e9dff06f          	j	58e4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>

00005a4c <exit>:
    5a4c:	0000006f          	j	5a4c <exit>
