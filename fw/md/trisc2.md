# trisc2

## Summary

| field | value |
| --- | ---: |
| kind | `trisc2` |
| base | `0x6640` |
| instructions | 149 |
| text bytes | 596 (`0x254`) |

## Segments

| label | address | size | flags |
| --- | ---: | ---: | --- |
| `trisc2.text` | `0x6640` | 596 (`0x254`) | `RX` |
| `trisc2.local_data` | `0xe2b0` | 1056 (`0x420`) | `RW` |

## Disassembly

```python
; trisc2: blackhole-py firmware

  00006640:  ffb001b7  lui(gp, 0xFFB00000)  # gp=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006644:  7f018193  addi(gp, gp, 0x7F0)  # gp=TRISC_GLOBAL_POINTER (RISC_LOCAL_RAM+0x7f0)
  00006648:  ffb01137  lui(sp, 0xFFB01000)  # sp=TRISC_STACK_TOP+0x10 (RISC_LOCAL_RAM+0x1000)
  0000664c:  ff010113  addi(sp, sp, -16)  # sp=TRISC_STACK_TOP (RISC_LOCAL_RAM+0xff0)
  00006650:  00200293  addi(t0, zero, 2)
  00006654:  7c02a073  csrrs(zero, t0, 0x7C0)
  00006658:  00100293  addi(t0, zero, 1)
  0000665c:  01229293  slli(t0, t0, 0x12)
  00006660:  0ff0000f  fence()
  00006664:  7c02a073  csrrs(zero, t0, 0x7C0)
  00006668:  00200293  addi(t0, zero, 2)
  0000666c:  7c02b073  csrrc(zero, t0, 0x7C0)
  00006670:  0ff0000f  fence()
  00006674:  0ff0000f  fence()
  00006678:  00800293  addi(t0, zero, 8)
  0000667c:  7c02a073  csrrs(zero, t0, 0x7C0)
  00006680:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006684:  0000e337  lui(t1, 0xE000)  # t1=L1+0xe000
  00006688:  2b030313  addi(t1, t1, 0x2B0)  # t1=TensixL1.TRISC2_INIT_LOCAL_L1_BASE_SCRATCH (L1+0xe2b0)
  0000668c:  10800e13  addi(t3, zero, 0x108)
.Lcopy_words_1:
  00006690:  000e0e63  beq(t3, zero, .Lcopy_done_2)  # beq(t3, zero, 0x1C)
  00006694:  00032383  lw(t2, t1, 0)  # [TensixL1.TRISC2_INIT_LOCAL_L1_BASE_SCRATCH (L1+0xe2b0)]
  00006698:  0072a023  sw(t2, t0, 0)  # [LOCAL_RAM_START (RISC_LOCAL_RAM)]
  0000669c:  00430313  addi(t1, t1, 4)  # t1=TensixL1.TRISC2_INIT_LOCAL_L1_BASE_SCRATCH+0x4 (L1+0xe2b4)
  000066a0:  00428293  addi(t0, t0, 4)  # t0=MY_Y (RISC_LOCAL_RAM+0x4)
  000066a4:  fffe0e13  addi(t3, t3, -1)
  000066a8:  fe9ff06f  jal(zero, .Lcopy_words_1)  # jal(zero, -24)
.Lcopy_done_2:
  000066ac:  ffe002b7  lui(t0, 0xFFE00000)  # t0=REGFILE_BASE
  000066b0:  04000313  addi(t1, zero, 0x40)
.Lzero_regfile_3:
  000066b4:  00030a63  beq(t1, zero, .Lzero_regfile_done_4)  # beq(t1, zero, 0x14)
  000066b8:  0002a023  sw(zero, t0, 0)  # [REGFILE_BASE]
  000066bc:  00428293  addi(t0, t0, 4)  # t0=REGFILE_BASE+0x4
  000066c0:  fff30313  addi(t1, t1, -1)
  000066c4:  ff1ff06f  jal(zero, .Lzero_regfile_3)  # jal(zero, -16)
.Lzero_regfile_done_4:
  000066c8:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000066cc:  00000313  addi(t1, zero, 0)
  000066d0:  0062a023  sw(t1, t0, 0)  # [LOCAL_RAM_START (RISC_LOCAL_RAM)]
  000066d4:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000066d8:  00428293  addi(t0, t0, 4)  # t0=MY_Y (RISC_LOCAL_RAM+0x4)
  000066dc:  00000313  addi(t1, zero, 0)
  000066e0:  0062a023  sw(t1, t0, 0)  # [MY_Y (RISC_LOCAL_RAM+0x4)]
  000066e4:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000066e8:  01c28293  addi(t0, t0, 0x1C)  # t0=NOC_POSTED_WRITES_NUM_ISSUED (RISC_LOCAL_RAM+0x1c)
  000066ec:  00000313  addi(t1, zero, 0)
  000066f0:  0062a023  sw(t1, t0, 0)  # [NOC_POSTED_WRITES_NUM_ISSUED (RISC_LOCAL_RAM+0x1c)]
  000066f4:  ffef02b7  lui(t0, 0xFFEF0000)  # t0=TENSIX_CFG_BASE (TENSIX_CFG)
  000066f8:  2e828293  addi(t0, t0, 0x2E8)  # t0=RISCV_IC_INVALIDATE_INVALIDATE_ALL+0x4 (TENSIX_CFG+0x2e8)
  000066fc:  00000313  addi(t1, zero, 0)
  00006700:  0062a023  sw(t1, t0, 0)  # [RISCV_IC_INVALIDATE_INVALIDATE_ALL+0x4 (TENSIX_CFG+0x2e8)]
  00006704:  25800293  addi(t0, zero, 0x258)
.Lwait_cycles_5:
  00006708:  00028663  beq(t0, zero, .Lwait_cycles_done_6)  # beq(t0, zero, 0xC)
  0000670c:  fff28293  addi(t0, t0, -1)
  00006710:  ff9ff06f  jal(zero, .Lwait_cycles_5)  # jal(zero, -8)
.Lwait_cycles_done_6:
  00006714:  000012b7  lui(t0, 0x1000)  # t0=STREAM_STRIDE (L1+0x1000)
  00006718:  94028293  addi(t0, t0, -1728)  # t0=CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)
  0000671c:  0002c303  lbu(t1, t0, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)]
  00006720:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006724:  01928293  addi(t0, t0, 0x19)  # t0=RTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x19)
  00006728:  00628023  sb(t1, t0, 0)  # [RTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x19)]
  0000672c:  000012b7  lui(t0, 0x1000)  # t0=STREAM_STRIDE (L1+0x1000)
  00006730:  94128293  addi(t0, t0, -1727)  # t0=CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)
  00006734:  0002c303  lbu(t1, t0, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)]
  00006738:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  0000673c:  01828293  addi(t0, t0, 0x18)  # t0=RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)
  00006740:  00628023  sb(t1, t0, 0)  # [RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)]
  00006744:  06b00293  addi(t0, zero, 0x6B)
  00006748:  00000313  addi(t1, zero, 0)
  0000674c:  00628023  sb(t1, t0, 0)
run_loop:
  00006750:  06b00293  addi(t0, zero, 0x6B)
.Lwait_trisc_7:
  00006754:  0002c303  lbu(t1, t0, 0)
  00006758:  08000393  addi(t2, zero, 0x80)
  0000675c:  00730663  beq(t1, t2, .Ltrisc_go_8)  # beq(t1, t2, 0xC)
  00006760:  0ff0000f  fence()
  00006764:  ff1ff06f  jal(zero, .Lwait_trisc_7)  # jal(zero, -16)
.Ltrisc_go_8:
  00006768:  0ff0000f  fence()
  0000676c:  07000293  addi(t0, zero, 0x70)
  00006770:  0002a303  lw(t1, t0, 0)
  00006774:  0122d383  lhu(t2, t0, 0x12)
  00006778:  007303b3  add(t2, t1, t2)
  0000677c:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006780:  020e0e13  addi(t3, t3, 0x20)  # t3=NOC_POSTED_WRITES_NUM_ISSUED+0x4 (RISC_LOCAL_RAM+0x20)
  00006784:  0402ae83  lw(t4, t0, 0x40)
.Lsetup_cb_10:
  00006788:  040e8c63  beq(t4, zero, .Ldone_cb_12)  # beq(t4, zero, 0x58)
  0000678c:  001ef313  andi(t1, t4, 1)
  00006790:  04030063  beq(t1, zero, .Lskip_cb_11)  # beq(t1, zero, 0x40)
  00006794:  0043af03  lw(t5, t2, 4)
  00006798:  0003af83  lw(t6, t2, 0)
  0000679c:  00c3a283  lw(t0, t2, 0xC)
  000067a0:  004f5f13  srli(t5, t5, 4)
  000067a4:  004fdf93  srli(t6, t6, 4)
  000067a8:  0042d293  srli(t0, t0, 4)
  000067ac:  01ee2023  sw(t5, t3, 0)  # [NOC_POSTED_WRITES_NUM_ISSUED+0x4 (RISC_LOCAL_RAM+0x20)]
  000067b0:  01ef8f33  add(t5, t6, t5)
  000067b4:  01ee2223  sw(t5, t3, 4)  # [NOC_NONPOSTED_ATOMICS_ACKED (RISC_LOCAL_RAM+0x24)]
  000067b8:  005e2423  sw(t0, t3, 8)  # [NOC_NONPOSTED_ATOMICS_ACKED+0x4 (RISC_LOCAL_RAM+0x28)]
  000067bc:  0083a303  lw(t1, t2, 8)
  000067c0:  006e2623  sw(t1, t3, 0xC)  # [NOC_NONPOSTED_WRITES_ACKED (RISC_LOCAL_RAM+0x2c)]
  000067c4:  01fe2a23  sw(t6, t3, 0x14)  # [CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x34)]
  000067c8:  000e2c23  sw(zero, t3, 0x18)  # [RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x38)]
  000067cc:  000e2e23  sw(zero, t3, 0x1C)  # [NOC_READS_NUM_ISSUED (RISC_LOCAL_RAM+0x3c)]
.Lskip_cb_11:
  000067d0:  01038393  addi(t2, t2, 0x10)
  000067d4:  020e0e13  addi(t3, t3, 0x20)  # t3=DRAM_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x40)
  000067d8:  001ede93  srli(t4, t4, 1)
  000067dc:  fadff06f  jal(zero, .Lsetup_cb_10)  # jal(zero, -84)
.Ldone_cb_12:
  000067e0:  07000293  addi(t0, zero, 0x70)
  000067e4:  0002a303  lw(t1, t0, 0)
  000067e8:  0262d383  lhu(t2, t0, 0x26)
  000067ec:  00730e33  add(t3, t1, t2)
  000067f0:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000067f4:  014e8e93  addi(t4, t4, 0x14)  # t4=CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x14)
  000067f8:  01cea023  sw(t3, t4, 0)  # [CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x14)]
  000067fc:  0282d383  lhu(t2, t0, 0x28)
  00006800:  00730e33  add(t3, t1, t2)
  00006804:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006808:  010e8e93  addi(t4, t4, 0x10)  # t4=MY_X+0x8 (RISC_LOCAL_RAM+0x10)
  0000680c:  01cea023  sw(t3, t4, 0)  # [MY_X+0x8 (RISC_LOCAL_RAM+0x10)]
  00006810:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006814:  019e0e13  addi(t3, t3, 0x19)  # t3=RTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x19)
  00006818:  000e4e83  lbu(t4, t3, 0)  # [RTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x19)]
  0000681c:  05c2cf03  lbu(t5, t0, 0x5C)
  00006820:  41ee8eb3  sub(t4, t4, t5)
  00006824:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006828:  00de0e13  addi(t3, t3, 0xD)  # t3=MY_X+0x5 (RISC_LOCAL_RAM+0xd)
  0000682c:  01de0023  sb(t4, t3, 0)  # [MY_X+0x5 (RISC_LOCAL_RAM+0xd)]
  00006830:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006834:  018e0e13  addi(t3, t3, 0x18)  # t3=RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)
  00006838:  000e4e83  lbu(t4, t3, 0)  # [RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)]
  0000683c:  05d2cf03  lbu(t5, t0, 0x5D)
  00006840:  41ee8eb3  sub(t4, t4, t5)
  00006844:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006848:  00ce0e13  addi(t3, t3, 0xC)  # t3=MY_X+0x4 (RISC_LOCAL_RAM+0xc)
  0000684c:  01de0023  sb(t4, t3, 0)  # [MY_X+0x4 (RISC_LOCAL_RAM+0xc)]
  00006850:  07000293  addi(t0, zero, 0x70)
  00006854:  0002a303  lw(t1, t0, 0)
  00006858:  03c2a383  lw(t2, t0, 0x3C)
  0000685c:  00730e33  add(t3, t1, t2)
  00006860:  000e00e7  jalr(ra, t3)
  00006864:  ffe802b7  lui(t0, 0xFFE80000)
  00006868:  00428293  addi(t0, t0, 4)  # t0=PC_BUF_SYNC
  0000686c:  00000313  addi(t1, zero, 0)
  00006870:  0062a023  sw(t1, t0, 0)  # [PC_BUF_SYNC]
  00006874:  ffe802b7  lui(t0, 0xFFE80000)
  00006878:  00428293  addi(t0, t0, 4)  # t0=PC_BUF_SYNC
  0000687c:  0002a283  lw(t0, t0, 0)  # [PC_BUF_SYNC]
  00006880:  00507033  and(zero, zero, t0)
  00006884:  06b00293  addi(t0, zero, 0x6B)
  00006888:  00000313  addi(t1, zero, 0)
  0000688c:  00628023  sb(t1, t0, 0)
  00006890:  ec1ff06f  jal(zero, run_loop)  # jal(zero, -320)
```
