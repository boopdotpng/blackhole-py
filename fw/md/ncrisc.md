# ncrisc

## Summary

| field | value |
| --- | ---: |
| kind | `ncrisc` |
| base | `0x5440` |
| instructions | 211 |
| text bytes | 844 (`0x34c`) |

## Segments

| label | address | size | flags |
| --- | ---: | ---: | --- |
| `ncrisc.text` | `0x5440` | 844 (`0x34c`) | `RX` |

## Disassembly

```python
; ncrisc: blackhole-py firmware

  00005440:  ffb02137  lui(sp, 0xFFB02000)  # sp=LOCAL_RAM_END+1 (RISC_LOCAL_RAM_END+1)
  00005444:  ff010113  addi(sp, sp, -16)  # sp=NCRISC_STACK_TOP (RISC_LOCAL_RAM+0x1ff0)
  00005448:  00200293  addi(t0, zero, 2)
  0000544c:  7c02a073  csrrs(zero, t0, 0x7C0)
  00005450:  00100293  addi(t0, zero, 1)
  00005454:  01229293  slli(t0, t0, 0x12)
  00005458:  0ff0000f  fence()
  0000545c:  7c02a073  csrrs(zero, t0, 0x7C0)
  00005460:  00200293  addi(t0, zero, 2)
  00005464:  7c02b073  csrrc(zero, t0, 0x7C0)
  00005468:  0ff0000f  fence()
  0000546c:  0ff0000f  fence()
  00005470:  00800293  addi(t0, zero, 8)
  00005474:  7c02a073  csrrs(zero, t0, 0x7C0)
  00005478:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  0000547c:  04028293  addi(t0, t0, 0x40)  # t0=DRAM_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x40)
  00005480:  00011337  lui(t1, 0x11000)  # t1=L1+0x11000
  00005484:  2b030313  addi(t1, t1, 0x2B0)  # t1=MEM_BANK_TO_NOC_SCRATCH (L1+0x112b0)
  00005488:  00700e13  addi(t3, zero, 7)
.Lcopy_words_1:
  0000548c:  000e0e63  beq(t3, zero, .Lcopy_done_2)  # beq(t3, zero, 0x1C)
  00005490:  00032383  lw(t2, t1, 0)  # [MEM_BANK_TO_NOC_SCRATCH (L1+0x112b0)]
  00005494:  0072a023  sw(t2, t0, 0)  # [DRAM_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x40)]
  00005498:  00430313  addi(t1, t1, 4)  # t1=MEM_BANK_TO_NOC_SCRATCH+0x4 (L1+0x112b4)
  0000549c:  00428293  addi(t0, t0, 4)  # t0=MY_LOGICAL_Y (RISC_LOCAL_RAM+0x44)
  000054a0:  fffe0e13  addi(t3, t3, -1)
  000054a4:  fe9ff06f  jal(zero, .Lcopy_words_1)  # jal(zero, -24)
.Lcopy_done_2:
  000054a8:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000054ac:  05c28293  addi(t0, t0, 0x5C)  # t0=L1_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x5c)
  000054b0:  00011337  lui(t1, 0x11000)  # t1=L1+0x11000
  000054b4:  2cc30313  addi(t1, t1, 0x2CC)  # t1=MEM_BANK_TO_NOC_SCRATCH+0x1c (L1+0x112cc)
  000054b8:  07800e13  addi(t3, zero, 0x78)
.Lcopy_words_3:
  000054bc:  000e0e63  beq(t3, zero, .Lcopy_done_4)  # beq(t3, zero, 0x1C)
  000054c0:  00032383  lw(t2, t1, 0)  # [MEM_BANK_TO_NOC_SCRATCH+0x1c (L1+0x112cc)]
  000054c4:  0072a023  sw(t2, t0, 0)  # [L1_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x5c)]
  000054c8:  00430313  addi(t1, t1, 4)  # t1=MEM_BANK_TO_NOC_SCRATCH+0x20 (L1+0x112d0)
  000054cc:  00428293  addi(t0, t0, 4)  # t0=L1_BANK_TO_NOC_XY+0x4 (RISC_LOCAL_RAM+0x60)
  000054d0:  fffe0e13  addi(t3, t3, -1)
  000054d4:  fe9ff06f  jal(zero, .Lcopy_words_3)  # jal(zero, -24)
.Lcopy_done_4:
  000054d8:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000054dc:  23c28293  addi(t0, t0, 0x23C)  # t0=BANK_TO_DRAM_OFFSET (RISC_LOCAL_RAM+0x23c)
  000054e0:  00011337  lui(t1, 0x11000)  # t1=L1+0x11000
  000054e4:  4ac30313  addi(t1, t1, 0x4AC)  # t1=MEM_BANK_TO_NOC_SCRATCH+0x1fc (L1+0x114ac)
  000054e8:  00700e13  addi(t3, zero, 7)
.Lcopy_words_5:
  000054ec:  000e0e63  beq(t3, zero, .Lcopy_done_6)  # beq(t3, zero, 0x1C)
  000054f0:  00032383  lw(t2, t1, 0)  # [MEM_BANK_TO_NOC_SCRATCH+0x1fc (L1+0x114ac)]
  000054f4:  0072a023  sw(t2, t0, 0)  # [BANK_TO_DRAM_OFFSET (RISC_LOCAL_RAM+0x23c)]
  000054f8:  00430313  addi(t1, t1, 4)  # t1=MEM_BANK_TO_NOC_SCRATCH+0x200 (L1+0x114b0)
  000054fc:  00428293  addi(t0, t0, 4)  # t0=BANK_TO_DRAM_OFFSET+0x4 (RISC_LOCAL_RAM+0x240)
  00005500:  fffe0e13  addi(t3, t3, -1)
  00005504:  fe9ff06f  jal(zero, .Lcopy_words_5)  # jal(zero, -24)
.Lcopy_done_6:
  00005508:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  0000550c:  25828293  addi(t0, t0, 0x258)  # t0=BANK_TO_L1_OFFSET (RISC_LOCAL_RAM+0x258)
  00005510:  00011337  lui(t1, 0x11000)  # t1=L1+0x11000
  00005514:  4c830313  addi(t1, t1, 0x4C8)  # t1=L1+0x114c8
  00005518:  07800e13  addi(t3, zero, 0x78)
.Lcopy_words_7:
  0000551c:  000e0e63  beq(t3, zero, .Lcopy_done_8)  # beq(t3, zero, 0x1C)
  00005520:  00032383  lw(t2, t1, 0)  # [L1+0x114c8]
  00005524:  0072a023  sw(t2, t0, 0)  # [BANK_TO_L1_OFFSET (RISC_LOCAL_RAM+0x258)]
  00005528:  00430313  addi(t1, t1, 4)  # t1=L1+0x114cc
  0000552c:  00428293  addi(t0, t0, 4)  # t0=BANK_TO_L1_OFFSET+0x4 (RISC_LOCAL_RAM+0x25c)
  00005530:  fffe0e13  addi(t3, t3, -1)
  00005534:  fe9ff06f  jal(zero, .Lcopy_words_7)  # jal(zero, -24)
.Lcopy_done_8:
  00005538:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  0000553c:  14838393  addi(t2, t2, 0x148)  # t2=NOC_CFG_BASE+0x48 (NOC0+0x148)
  00005540:  0003a283  lw(t0, t2, 0)  # [NOC_CFG_BASE+0x48 (NOC0+0x148)]
  00005544:  03f2f313  andi(t1, t0, 0x3F)
  00005548:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  0000554c:  03038393  addi(t2, t2, 0x30)  # t2=MY_X (RISC_LOCAL_RAM+0x30)
  00005550:  00638023  sb(t1, t2, 0)  # [MY_X (RISC_LOCAL_RAM+0x30)]
  00005554:  0062d313  srli(t1, t0, 6)
  00005558:  03f37313  andi(t1, t1, 0x3F)
  0000555c:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005560:  02c38393  addi(t2, t2, 0x2C)  # t2=NOC_NONPOSTED_WRITES_ACKED (RISC_LOCAL_RAM+0x2c)
  00005564:  00638023  sb(t1, t2, 0)  # [NOC_NONPOSTED_WRITES_ACKED (RISC_LOCAL_RAM+0x2c)]
  00005568:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  0000556c:  14838393  addi(t2, t2, 0x148)  # t2=NOC1+0x148
  00005570:  0003a283  lw(t0, t2, 0)  # [NOC1+0x148]
  00005574:  03f2f313  andi(t1, t0, 0x3F)
  00005578:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  0000557c:  03138393  addi(t2, t2, 0x31)  # t2=MY_X+0x1 (RISC_LOCAL_RAM+0x31)
  00005580:  00638023  sb(t1, t2, 0)  # [MY_X+0x1 (RISC_LOCAL_RAM+0x31)]
  00005584:  0062d313  srli(t1, t0, 6)
  00005588:  03f37313  andi(t1, t1, 0x3F)
  0000558c:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005590:  02d38393  addi(t2, t2, 0x2D)  # t2=NOC_NONPOSTED_WRITES_ACKED+0x1 (RISC_LOCAL_RAM+0x2d)
  00005594:  00638023  sb(t1, t2, 0)  # [NOC_NONPOSTED_WRITES_ACKED+0x1 (RISC_LOCAL_RAM+0x2d)]
  00005598:  00001337  lui(t1, 0x1000)  # t1=STREAM_STRIDE (L1+0x1000)
  0000559c:  94030313  addi(t1, t1, -1728)  # t1=CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)
  000055a0:  00034283  lbu(t0, t1, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)]
  000055a4:  ffb00337  lui(t1, 0xFFB00000)  # t1=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000055a8:  03d30313  addi(t1, t1, 0x3D)  # t1=MY_LOGICAL_X (RISC_LOCAL_RAM+0x3d)
  000055ac:  00530023  sb(t0, t1, 0)  # [MY_LOGICAL_X (RISC_LOCAL_RAM+0x3d)]
  000055b0:  00001337  lui(t1, 0x1000)  # t1=STREAM_STRIDE (L1+0x1000)
  000055b4:  94130313  addi(t1, t1, -1727)  # t1=CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)
  000055b8:  00034283  lbu(t0, t1, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)]
  000055bc:  ffb00337  lui(t1, 0xFFB00000)  # t1=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000055c0:  03c30313  addi(t1, t1, 0x3C)  # t1=NOC_READS_NUM_ISSUED (RISC_LOCAL_RAM+0x3c)
  000055c4:  00530023  sb(t0, t1, 0)  # [NOC_READS_NUM_ISSUED (RISC_LOCAL_RAM+0x3c)]
  000055c8:  06800293  addi(t0, zero, 0x68)
  000055cc:  00000313  addi(t1, zero, 0)
  000055d0:  00628023  sb(t1, t0, 0)
run_loop:
  000055d4:  06800293  addi(t0, zero, 0x68)
.Lwait_subordinate_9:
  000055d8:  0002c303  lbu(t1, t0, 0)
  000055dc:  08000393  addi(t2, zero, 0x80)
  000055e0:  00730a63  beq(t1, t2, .Lsubordinate_ready_10)  # beq(t1, t2, 0x14)
  000055e4:  00100393  addi(t2, zero, 1)
  000055e8:  00730663  beq(t1, t2, .Lsubordinate_ready_10)  # beq(t1, t2, 0xC)
  000055ec:  0ff0000f  fence()
  000055f0:  fe9ff06f  jal(zero, .Lwait_subordinate_9)  # jal(zero, -24)
.Lsubordinate_ready_10:
  000055f4:  0ff0000f  fence()
  000055f8:  07000293  addi(t0, zero, 0x70)
  000055fc:  0002a303  lw(t1, t0, 0)
  00005600:  00c2d383  lhu(t2, t0, 0xC)
  00005604:  00730e33  add(t3, t1, t2)
  00005608:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  0000560c:  458e8e93  addi(t4, t4, 0x458)  # t4=SEM_L1_BASE (RISC_LOCAL_RAM+0x458)
  00005610:  01cea023  sw(t3, t4, 0)  # [SEM_L1_BASE (RISC_LOCAL_RAM+0x458)]
  00005614:  00e2d383  lhu(t2, t0, 0xE)
  00005618:  00730e33  add(t3, t1, t2)
  0000561c:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005620:  45ce8e93  addi(t4, t4, 0x45C)  # t4=SEM_L1_BASE+0x4 (RISC_LOCAL_RAM+0x45c)
  00005624:  01cea023  sw(t3, t4, 0)  # [SEM_L1_BASE+0x4 (RISC_LOCAL_RAM+0x45c)]
  00005628:  0102d383  lhu(t2, t0, 0x10)
  0000562c:  00730e33  add(t3, t1, t2)
  00005630:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005634:  460e8e93  addi(t4, t4, 0x460)  # t4=SEM_L1_BASE+0x8 (RISC_LOCAL_RAM+0x460)
  00005638:  01cea023  sw(t3, t4, 0)  # [SEM_L1_BASE+0x8 (RISC_LOCAL_RAM+0x460)]
  0000563c:  01a2d383  lhu(t2, t0, 0x1A)
  00005640:  00730e33  add(t3, t1, t2)
  00005644:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005648:  038e8e93  addi(t4, t4, 0x38)  # t4=RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x38)
  0000564c:  01cea023  sw(t3, t4, 0)  # [RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x38)]
  00005650:  01c2d383  lhu(t2, t0, 0x1C)
  00005654:  00730e33  add(t3, t1, t2)
  00005658:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  0000565c:  034e8e93  addi(t4, t4, 0x34)  # t4=CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x34)
  00005660:  01cea023  sw(t3, t4, 0)  # [CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x34)]
  00005664:  07000293  addi(t0, zero, 0x70)
  00005668:  0002a303  lw(t1, t0, 0)
  0000566c:  0122d383  lhu(t2, t0, 0x12)
  00005670:  007303b3  add(t2, t1, t2)
  00005674:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005678:  464e0e13  addi(t3, t3, 0x464)  # t3=L1_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x464)
  0000567c:  0402ae83  lw(t4, t0, 0x40)
  00005680:  ffb482b7  lui(t0, 0xFFB48000)  # t0=STREAM_REGS+0x8000
  00005684:  02028293  addi(t0, t0, 0x20)  # t0=CB_SYNC_TILES_ACKED_BASE (STREAM_REGS+0x8020)
  00005688:  ffb48337  lui(t1, 0xFFB48000)  # t1=STREAM_REGS+0x8000
  0000568c:  02830313  addi(t1, t1, 0x28)  # t1=CB_SYNC_TILES_RECEIVED_BASE (STREAM_REGS+0x8028)
.Lsetup_cb_11:
  00005690:  060e8263  beq(t4, zero, .Ldone_cb_13)  # beq(t4, zero, 0x64)
  00005694:  001eff13  andi(t5, t4, 1)
  00005698:  040f0063  beq(t5, zero, .Lskip_cb_12)  # beq(t5, zero, 0x40)
  0000569c:  0043af03  lw(t5, t2, 4)
  000056a0:  0003af83  lw(t6, t2, 0)
  000056a4:  01ee2023  sw(t5, t3, 0)  # [L1_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x464)]
  000056a8:  01ef8f33  add(t5, t6, t5)
  000056ac:  01ee2223  sw(t5, t3, 4)  # [L1_BANK_TO_NOC_XY+0x4 (RISC_LOCAL_RAM+0x468)]
  000056b0:  00c3af03  lw(t5, t2, 0xC)
  000056b4:  01ee2423  sw(t5, t3, 8)  # [L1_BANK_TO_NOC_XY+0x8 (RISC_LOCAL_RAM+0x46c)]
  000056b8:  0083af03  lw(t5, t2, 8)
  000056bc:  01ee2623  sw(t5, t3, 0xC)  # [L1_BANK_TO_NOC_XY+0xc (RISC_LOCAL_RAM+0x470)]
  000056c0:  01fe2823  sw(t6, t3, 0x10)  # [L1_BANK_TO_NOC_XY+0x10 (RISC_LOCAL_RAM+0x474)]
  000056c4:  01fe2a23  sw(t6, t3, 0x14)  # [L1_BANK_TO_NOC_XY+0x14 (RISC_LOCAL_RAM+0x478)]
  000056c8:  000e2c23  sw(zero, t3, 0x18)  # [L1_BANK_TO_NOC_XY+0x18 (RISC_LOCAL_RAM+0x47c)]
  000056cc:  000e2e23  sw(zero, t3, 0x1C)  # [L1_BANK_TO_NOC_XY+0x1c (RISC_LOCAL_RAM+0x480)]
  000056d0:  0002a023  sw(zero, t0, 0)  # [CB_SYNC_TILES_ACKED_BASE (STREAM_REGS+0x8020)]
  000056d4:  00032023  sw(zero, t1, 0)  # [CB_SYNC_TILES_RECEIVED_BASE (STREAM_REGS+0x8028)]
.Lskip_cb_12:
  000056d8:  01038393  addi(t2, t2, 0x10)
  000056dc:  020e0e13  addi(t3, t3, 0x20)  # t3=L1_BANK_TO_NOC_XY+0x20 (RISC_LOCAL_RAM+0x484)
  000056e0:  00001f37  lui(t5, 0x1000)  # t5=STREAM_STRIDE (L1+0x1000)
  000056e4:  01e282b3  add(t0, t0, t5)
  000056e8:  01e30333  add(t1, t1, t5)
  000056ec:  001ede93  srli(t4, t4, 1)
  000056f0:  fa1ff06f  jal(zero, .Lsetup_cb_11)  # jal(zero, -96)
.Ldone_cb_13:
  000056f4:  07000293  addi(t0, zero, 0x70)
  000056f8:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000056fc:  03d38393  addi(t2, t2, 0x3D)  # t2=MY_LOGICAL_X (RISC_LOCAL_RAM+0x3d)
  00005700:  0003c303  lbu(t1, t2, 0)  # [MY_LOGICAL_X (RISC_LOCAL_RAM+0x3d)]
  00005704:  05c2ce03  lbu(t3, t0, 0x5C)
  00005708:  41c30333  sub(t1, t1, t3)
  0000570c:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005710:  03338393  addi(t2, t2, 0x33)  # t2=MY_RELATIVE_X (RISC_LOCAL_RAM+0x33)
  00005714:  00638023  sb(t1, t2, 0)  # [MY_RELATIVE_X (RISC_LOCAL_RAM+0x33)]
  00005718:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  0000571c:  03c38393  addi(t2, t2, 0x3C)  # t2=NOC_READS_NUM_ISSUED (RISC_LOCAL_RAM+0x3c)
  00005720:  0003c303  lbu(t1, t2, 0)  # [NOC_READS_NUM_ISSUED (RISC_LOCAL_RAM+0x3c)]
  00005724:  05d2ce03  lbu(t3, t0, 0x5D)
  00005728:  41c30333  sub(t1, t1, t3)
  0000572c:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005730:  03238393  addi(t2, t2, 0x32)  # t2=MY_RELATIVE_Y (RISC_LOCAL_RAM+0x32)
  00005734:  00638023  sb(t1, t2, 0)  # [MY_RELATIVE_Y (RISC_LOCAL_RAM+0x32)]
  00005738:  06800293  addi(t0, zero, 0x68)
  0000573c:  08000393  addi(t2, zero, 0x80)
.Lwait8_14:
  00005740:  0002c303  lbu(t1, t0, 0)
  00005744:  00730663  beq(t1, t2, .Lwait8_done_15)  # beq(t1, t2, 0xC)
  00005748:  0ff0000f  fence()
  0000574c:  ff5ff06f  jal(zero, .Lwait8_14)  # jal(zero, -12)
.Lwait8_done_15:
  00005750:  0ff0000f  fence()
  00005754:  07000e93  addi(t4, zero, 0x70)
  00005758:  04ceae83  lw(t4, t4, 0x4C)
  0000575c:  00200393  addi(t2, zero, 2)
  00005760:  007efeb3  and(t4, t4, t2)
  00005764:  000e8c63  beq(t4, zero, .Lskip_kernel_16)  # beq(t4, zero, 0x18)
  00005768:  07000293  addi(t0, zero, 0x70)
  0000576c:  0002a303  lw(t1, t0, 0)
  00005770:  0302a383  lw(t2, t0, 0x30)
  00005774:  00730e33  add(t3, t1, t2)
  00005778:  000e00e7  jalr(ra, t3)
.Lskip_kernel_16:
  0000577c:  06800293  addi(t0, zero, 0x68)
  00005780:  00000313  addi(t1, zero, 0)
  00005784:  00628023  sb(t1, t0, 0)
  00005788:  e4dff06f  jal(zero, run_loop)  # jal(zero, -436)
```
