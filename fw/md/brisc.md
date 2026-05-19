# brisc

## Summary

| field | value |
| --- | ---: |
| kind | `brisc` |
| base | `0x3840` |
| instructions | 850 |
| text bytes | 3400 (`0xd48`) |

## Segments

| label | address | size | flags |
| --- | ---: | ---: | --- |
| `brisc.text` | `0x3840` | 3400 (`0xd48`) | `RX` |

## Disassembly

```python
; brisc: blackhole-py firmware

  00003840:  ffb02137  lui(sp, 0xFFB02000)  # sp=LOCAL_RAM_END+1 (RISC_LOCAL_RAM_END+1)
  00003844:  ff010113  addi(sp, sp, -16)  # sp=BRISC_STACK_TOP (RISC_LOCAL_RAM+0x1ff0)
  00003848:  ffb122b7  lui(t0, 0xFFB12000)  # t0=RISCV_DEBUG/RESET+0x2000
  0000384c:  23828293  addi(t0, t0, 0x238)  # t0=NCRISC_RESET_PC (RISCV_DEBUG/RESET+0x2238)
  00003850:  00005337  lui(t1, 0x5000)  # t1=L1+0x5000
  00003854:  44030313  addi(t1, t1, 0x440)  # t1=ncrisc.text (L1+0x5440)
  00003858:  0062a023  sw(t1, t0, 0)  # [NCRISC_RESET_PC (RISCV_DEBUG/RESET+0x2238)], value=ncrisc.text (L1+0x5440)
  0000385c:  ffb122b7  lui(t0, 0xFFB12000)  # t0=RISCV_DEBUG/RESET+0x2000
  00003860:  22828293  addi(t0, t0, 0x228)  # t0=TRISC0_RESET_PC (RISCV_DEBUG/RESET+0x2228)
  00003864:  00006337  lui(t1, 0x6000)  # t1=L1+0x6000
  00003868:  a4030313  addi(t1, t1, -1472)  # t1=trisc0.text (L1+0x5a40)
  0000386c:  0062a023  sw(t1, t0, 0)  # [TRISC0_RESET_PC (RISCV_DEBUG/RESET+0x2228)], value=trisc0.text (L1+0x5a40)
  00003870:  ffb122b7  lui(t0, 0xFFB12000)  # t0=RISCV_DEBUG/RESET+0x2000
  00003874:  22c28293  addi(t0, t0, 0x22C)  # t0=TRISC1_RESET_PC (RISCV_DEBUG/RESET+0x222c)
  00003878:  00006337  lui(t1, 0x6000)  # t1=L1+0x6000
  0000387c:  04030313  addi(t1, t1, 0x40)  # t1=trisc1.text (L1+0x6040)
  00003880:  0062a023  sw(t1, t0, 0)  # [TRISC1_RESET_PC (RISCV_DEBUG/RESET+0x222c)], value=trisc1.text (L1+0x6040)
  00003884:  ffb122b7  lui(t0, 0xFFB12000)  # t0=RISCV_DEBUG/RESET+0x2000
  00003888:  23028293  addi(t0, t0, 0x230)  # t0=TRISC2_RESET_PC (RISCV_DEBUG/RESET+0x2230)
  0000388c:  00006337  lui(t1, 0x6000)  # t1=L1+0x6000
  00003890:  64030313  addi(t1, t1, 0x640)  # t1=trisc2.text (L1+0x6640)
  00003894:  0062a023  sw(t1, t0, 0)  # [TRISC2_RESET_PC (RISCV_DEBUG/RESET+0x2230)], value=trisc2.text (L1+0x6640)
  00003898:  ffb122b7  lui(t0, 0xFFB12000)  # t0=RISCV_DEBUG/RESET+0x2000
  0000389c:  23428293  addi(t0, t0, 0x234)  # t0=TRISC_RESET_PC_OVERRIDE (RISCV_DEBUG/RESET+0x2234)
  000038a0:  00700313  addi(t1, zero, 7)
  000038a4:  0062a023  sw(t1, t0, 0)  # [TRISC_RESET_PC_OVERRIDE (RISCV_DEBUG/RESET+0x2234)]
  000038a8:  ffb122b7  lui(t0, 0xFFB12000)  # t0=RISCV_DEBUG/RESET+0x2000
  000038ac:  23c28293  addi(t0, t0, 0x23C)  # t0=NCRISC_RESET_PC_OVERRIDE (RISCV_DEBUG/RESET+0x223c)
  000038b0:  00100313  addi(t1, zero, 1)
  000038b4:  0062a023  sw(t1, t0, 0)  # [NCRISC_RESET_PC_OVERRIDE (RISCV_DEBUG/RESET+0x223c)]
  000038b8:  ffb122b7  lui(t0, 0xFFB12000)  # t0=RISCV_DEBUG/RESET+0x2000
  000038bc:  24028293  addi(t0, t0, 0x240)  # t0=RISCV_DEBUG_REG_DEST_CG_CTRL (RISCV_DEBUG/RESET+0x2240)
  000038c0:  00000313  addi(t1, zero, 0)
  000038c4:  0062a023  sw(t1, t0, 0)  # [RISCV_DEBUG_REG_DEST_CG_CTRL (RISCV_DEBUG/RESET+0x2240)]
  000038c8:  ffb112b7  lui(t0, 0xFFB11000)  # t0=RISCV_DEBUG/RESET+0x1000
  000038cc:  02428293  addi(t0, t0, 0x24)  # t0=RISCV_TDMA_REG_CLK_GATE_EN (RISCV_DEBUG/RESET+0x1024)
  000038d0:  03f00313  addi(t1, zero, 0x3F)
  000038d4:  0062a023  sw(t1, t0, 0)  # [RISCV_TDMA_REG_CLK_GATE_EN (RISCV_DEBUG/RESET+0x1024)]
  000038d8:  ffb202b7  lui(t0, 0xFFB20000)  # t0=NOC_TARG_ADDR_LO (NOC0)
  000038dc:  10028293  addi(t0, t0, 0x100)  # t0=NOC_CFG_BASE (NOC0+0x100)
  000038e0:  0002a303  lw(t1, t0, 0)  # [NOC_CFG_BASE (NOC0+0x100)]
  000038e4:  00136313  ori(t1, t1, 1)
  000038e8:  0062a023  sw(t1, t0, 0)  # [NOC_CFG_BASE (NOC0+0x100)]
  000038ec:  ffb202b7  lui(t0, 0xFFB20000)  # t0=NOC_TARG_ADDR_LO (NOC0)
  000038f0:  10428293  addi(t0, t0, 0x104)  # t0=NOC_CFG_BASE+0x4 (NOC0+0x104)
  000038f4:  0002a303  lw(t1, t0, 0)  # [NOC_CFG_BASE+0x4 (NOC0+0x104)]
  000038f8:  00136313  ori(t1, t1, 1)
  000038fc:  0062a023  sw(t1, t0, 0)  # [NOC_CFG_BASE+0x4 (NOC0+0x104)]
  00003900:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00003904:  10028293  addi(t0, t0, 0x100)  # t0=NOC1+0x100
  00003908:  0002a303  lw(t1, t0, 0)  # [NOC1+0x100]
  0000390c:  00136313  ori(t1, t1, 1)
  00003910:  0062a023  sw(t1, t0, 0)  # [NOC1+0x100]
  00003914:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00003918:  10428293  addi(t0, t0, 0x104)  # t0=NOC1+0x104
  0000391c:  0002a303  lw(t1, t0, 0)  # [NOC1+0x104]
  00003920:  00136313  ori(t1, t1, 1)
  00003924:  0062a023  sw(t1, t0, 0)  # [NOC1+0x104]
  00003928:  ffe402b7  lui(t0, 0xFFE40000)  # t0=INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)
  0000392c:  10180337  lui(t1, 0x10180000)
  00003930:  0062a023  sw(t1, t0, 0)  # [INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)]
  00003934:  ffe402b7  lui(t0, 0xFFE40000)  # t0=INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)
  00003938:  8a003337  lui(t1, 0x8A003000)
  0000393c:  00a30313  addi(t1, t1, 0xA)
  00003940:  0062a023  sw(t1, t0, 0)  # [INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)]
  00003944:  ffe402b7  lui(t0, 0xFFE40000)  # t0=INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)
  00003948:  02000337  lui(t1, 0x2000000)
  0000394c:  0062a023  sw(t1, t0, 0)  # [INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)], value=INSTRN_NOP
  00003950:  ffe402b7  lui(t0, 0xFFE40000)  # t0=INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)
  00003954:  7100c337  lui(t1, 0x7100C000)
  00003958:  f8030313  addi(t1, t1, -128)
  0000395c:  0062a023  sw(t1, t0, 0)  # [INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)]
  00003960:  ffe402b7  lui(t0, 0xFFE40000)  # t0=INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)
  00003964:  91000337  lui(t1, 0x91000000)
  00003968:  0b030313  addi(t1, t1, 0xB0)
  0000396c:  0062a023  sw(t1, t0, 0)  # [INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)]
  00003970:  ffe402b7  lui(t0, 0xFFE40000)  # t0=INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)
  00003974:  a3100337  lui(t1, 0xA3100000)
  00003978:  00830313  addi(t1, t1, 8)
  0000397c:  0062a023  sw(t1, t0, 0)  # [INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)]
  00003980:  ffe402b7  lui(t0, 0xFFE40000)  # t0=INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)
  00003984:  a3100337  lui(t1, 0xA3100000)
  00003988:  01030313  addi(t1, t1, 0x10)
  0000398c:  0062a023  sw(t1, t0, 0)  # [INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)]
  00003990:  ffe402b7  lui(t0, 0xFFE40000)  # t0=INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)
  00003994:  a3100337  lui(t1, 0xA3100000)
  00003998:  20030313  addi(t1, t1, 0x200)
  0000399c:  0062a023  sw(t1, t0, 0)  # [INSTRN_BUF_BASE (TENSIX_INSTRN_BUF)]
  000039a0:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  000039a4:  14838393  addi(t2, t2, 0x148)  # t2=NOC_CFG_BASE+0x48 (NOC0+0x148)
  000039a8:  0003a283  lw(t0, t2, 0)  # [NOC_CFG_BASE+0x48 (NOC0+0x148)]
  000039ac:  03f2f313  andi(t1, t0, 0x3F)
  000039b0:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000039b4:  00838393  addi(t2, t2, 8)  # t2=MY_X (RISC_LOCAL_RAM+0x8)
  000039b8:  00638023  sb(t1, t2, 0)  # [MY_X (RISC_LOCAL_RAM+0x8)]
  000039bc:  0062d313  srli(t1, t0, 6)
  000039c0:  03f37313  andi(t1, t1, 0x3F)
  000039c4:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000039c8:  00438393  addi(t2, t2, 4)  # t2=MY_Y (RISC_LOCAL_RAM+0x4)
  000039cc:  00638023  sb(t1, t2, 0)  # [MY_Y (RISC_LOCAL_RAM+0x4)]
  000039d0:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  000039d4:  14838393  addi(t2, t2, 0x148)  # t2=NOC1+0x148
  000039d8:  0003a283  lw(t0, t2, 0)  # [NOC1+0x148]
  000039dc:  03f2f313  andi(t1, t0, 0x3F)
  000039e0:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000039e4:  00938393  addi(t2, t2, 9)  # t2=MY_X+0x1 (RISC_LOCAL_RAM+0x9)
  000039e8:  00638023  sb(t1, t2, 0)  # [MY_X+0x1 (RISC_LOCAL_RAM+0x9)]
  000039ec:  0062d313  srli(t1, t0, 6)
  000039f0:  03f37313  andi(t1, t1, 0x3F)
  000039f4:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000039f8:  00538393  addi(t2, t2, 5)  # t2=MY_Y+0x1 (RISC_LOCAL_RAM+0x5)
  000039fc:  00638023  sb(t1, t2, 0)  # [MY_Y+0x1 (RISC_LOCAL_RAM+0x5)]
  00003a00:  ffef02b7  lui(t0, 0xFFEF0000)  # t0=TENSIX_CFG_BASE (TENSIX_CFG)
  00003a04:  2e428293  addi(t0, t0, 0x2E4)  # t0=RISCV_IC_INVALIDATE_INVALIDATE_ALL (TENSIX_CFG+0x2e4)
  00003a08:  01f00313  addi(t1, zero, 0x1F)
  00003a0c:  0062a023  sw(t1, t0, 0)  # [RISCV_IC_INVALIDATE_INVALIDATE_ALL (TENSIX_CFG+0x2e4)]
  00003a10:  ffb122b7  lui(t0, 0xFFB12000)  # t0=RISCV_DEBUG/RESET+0x2000
  00003a14:  1b028293  addi(t0, t0, 0x1B0)  # t0=SOFT_RESET_0 (RISCV_DEBUG/RESET+0x21b0)
  00003a18:  00000313  addi(t1, zero, 0)
  00003a1c:  0062a023  sw(t1, t0, 0)  # [SOFT_RESET_0 (RISCV_DEBUG/RESET+0x21b0)]
  00003a20:  06800293  addi(t0, zero, 0x68)
  00003a24:  00000393  addi(t2, zero, 0)
.Lwait8_1:
  00003a28:  0002c303  lbu(t1, t0, 0)
  00003a2c:  00730663  beq(t1, t2, .Lwait8_done_2)  # beq(t1, t2, 0xC)
  00003a30:  0ff0000f  fence()
  00003a34:  ff5ff06f  jal(zero, .Lwait8_1)  # jal(zero, -12)
.Lwait8_done_2:
  00003a38:  0ff0000f  fence()
  00003a3c:  06900293  addi(t0, zero, 0x69)
  00003a40:  00000393  addi(t2, zero, 0)
.Lwait8_3:
  00003a44:  0002c303  lbu(t1, t0, 0)
  00003a48:  00730663  beq(t1, t2, .Lwait8_done_4)  # beq(t1, t2, 0xC)
  00003a4c:  0ff0000f  fence()
  00003a50:  ff5ff06f  jal(zero, .Lwait8_3)  # jal(zero, -12)
.Lwait8_done_4:
  00003a54:  0ff0000f  fence()
  00003a58:  06a00293  addi(t0, zero, 0x6A)
  00003a5c:  00000393  addi(t2, zero, 0)
.Lwait8_5:
  00003a60:  0002c303  lbu(t1, t0, 0)
  00003a64:  00730663  beq(t1, t2, .Lwait8_done_6)  # beq(t1, t2, 0xC)
  00003a68:  0ff0000f  fence()
  00003a6c:  ff5ff06f  jal(zero, .Lwait8_5)  # jal(zero, -12)
.Lwait8_done_6:
  00003a70:  0ff0000f  fence()
  00003a74:  06b00293  addi(t0, zero, 0x6B)
  00003a78:  00000393  addi(t2, zero, 0)
.Lwait8_7:
  00003a7c:  0002c303  lbu(t1, t0, 0)
  00003a80:  00730663  beq(t1, t2, .Lwait8_done_8)  # beq(t1, t2, 0xC)
  00003a84:  0ff0000f  fence()
  00003a88:  ff5ff06f  jal(zero, .Lwait8_7)  # jal(zero, -12)
.Lwait8_done_8:
  00003a8c:  0ff0000f  fence()
  00003a90:  37300293  addi(t0, zero, 0x373)
  00003a94:  00000313  addi(t1, zero, 0)
  00003a98:  00628023  sb(t1, t0, 0)
  00003a9c:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003aa0:  44828293  addi(t0, t0, 0x448)  # t0=DRAM_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x448)
  00003aa4:  00011337  lui(t1, 0x11000)  # t1=L1+0x11000
  00003aa8:  2b030313  addi(t1, t1, 0x2B0)  # t1=MEM_BANK_TO_NOC_SCRATCH (L1+0x112b0)
  00003aac:  00700e13  addi(t3, zero, 7)
.Lcopy_words_9:
  00003ab0:  000e0e63  beq(t3, zero, .Lcopy_done_10)  # beq(t3, zero, 0x1C)
  00003ab4:  00032383  lw(t2, t1, 0)  # [MEM_BANK_TO_NOC_SCRATCH (L1+0x112b0)]
  00003ab8:  0072a023  sw(t2, t0, 0)  # [DRAM_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x448)]
  00003abc:  00430313  addi(t1, t1, 4)  # t1=MEM_BANK_TO_NOC_SCRATCH+0x4 (L1+0x112b4)
  00003ac0:  00428293  addi(t0, t0, 4)  # t0=DRAM_BANK_TO_NOC_XY+0x4 (RISC_LOCAL_RAM+0x44c)
  00003ac4:  fffe0e13  addi(t3, t3, -1)
  00003ac8:  fe9ff06f  jal(zero, .Lcopy_words_9)  # jal(zero, -24)
.Lcopy_done_10:
  00003acc:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003ad0:  46428293  addi(t0, t0, 0x464)  # t0=L1_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x464)
  00003ad4:  00011337  lui(t1, 0x11000)  # t1=L1+0x11000
  00003ad8:  2cc30313  addi(t1, t1, 0x2CC)  # t1=MEM_BANK_TO_NOC_SCRATCH+0x1c (L1+0x112cc)
  00003adc:  07800e13  addi(t3, zero, 0x78)
.Lcopy_words_11:
  00003ae0:  000e0e63  beq(t3, zero, .Lcopy_done_12)  # beq(t3, zero, 0x1C)
  00003ae4:  00032383  lw(t2, t1, 0)  # [MEM_BANK_TO_NOC_SCRATCH+0x1c (L1+0x112cc)]
  00003ae8:  0072a023  sw(t2, t0, 0)  # [L1_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x464)]
  00003aec:  00430313  addi(t1, t1, 4)  # t1=MEM_BANK_TO_NOC_SCRATCH+0x20 (L1+0x112d0)
  00003af0:  00428293  addi(t0, t0, 4)  # t0=L1_BANK_TO_NOC_XY+0x4 (RISC_LOCAL_RAM+0x468)
  00003af4:  fffe0e13  addi(t3, t3, -1)
  00003af8:  fe9ff06f  jal(zero, .Lcopy_words_11)  # jal(zero, -24)
.Lcopy_done_12:
  00003afc:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003b00:  64428293  addi(t0, t0, 0x644)  # t0=BANK_TO_DRAM_OFFSET (RISC_LOCAL_RAM+0x644)
  00003b04:  00011337  lui(t1, 0x11000)  # t1=L1+0x11000
  00003b08:  4ac30313  addi(t1, t1, 0x4AC)  # t1=MEM_BANK_TO_NOC_SCRATCH+0x1fc (L1+0x114ac)
  00003b0c:  00700e13  addi(t3, zero, 7)
.Lcopy_words_13:
  00003b10:  000e0e63  beq(t3, zero, .Lcopy_done_14)  # beq(t3, zero, 0x1C)
  00003b14:  00032383  lw(t2, t1, 0)  # [MEM_BANK_TO_NOC_SCRATCH+0x1fc (L1+0x114ac)]
  00003b18:  0072a023  sw(t2, t0, 0)  # [BANK_TO_DRAM_OFFSET (RISC_LOCAL_RAM+0x644)]
  00003b1c:  00430313  addi(t1, t1, 4)  # t1=MEM_BANK_TO_NOC_SCRATCH+0x200 (L1+0x114b0)
  00003b20:  00428293  addi(t0, t0, 4)  # t0=BANK_TO_DRAM_OFFSET+0x4 (RISC_LOCAL_RAM+0x648)
  00003b24:  fffe0e13  addi(t3, t3, -1)
  00003b28:  fe9ff06f  jal(zero, .Lcopy_words_13)  # jal(zero, -24)
.Lcopy_done_14:
  00003b2c:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003b30:  66028293  addi(t0, t0, 0x660)  # t0=BANK_TO_L1_OFFSET (RISC_LOCAL_RAM+0x660)
  00003b34:  00011337  lui(t1, 0x11000)  # t1=L1+0x11000
  00003b38:  4c830313  addi(t1, t1, 0x4C8)  # t1=L1+0x114c8
  00003b3c:  07800e13  addi(t3, zero, 0x78)
.Lcopy_words_15:
  00003b40:  000e0e63  beq(t3, zero, .Lcopy_done_16)  # beq(t3, zero, 0x1C)
  00003b44:  00032383  lw(t2, t1, 0)  # [L1+0x114c8]
  00003b48:  0072a023  sw(t2, t0, 0)  # [BANK_TO_L1_OFFSET (RISC_LOCAL_RAM+0x660)]
  00003b4c:  00430313  addi(t1, t1, 4)  # t1=L1+0x114cc
  00003b50:  00428293  addi(t0, t0, 4)  # t0=BANK_TO_L1_OFFSET+0x4 (RISC_LOCAL_RAM+0x664)
  00003b54:  fffe0e13  addi(t3, t3, -1)
  00003b58:  fe9ff06f  jal(zero, .Lcopy_words_15)  # jal(zero, -24)
.Lcopy_done_16:
  00003b5c:  06c00313  addi(t1, zero, 0x6C)
  00003b60:  00000293  addi(t0, zero, 0)
  00003b64:  00532023  sw(t0, t1, 0)
  00003b68:  ffb00337  lui(t1, 0xFFB00000)  # t1=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003b6c:  04630313  addi(t1, t1, 0x46)  # t1=NOC_INDEX (RISC_LOCAL_RAM+0x46)
  00003b70:  00000293  addi(t0, zero, 0)
  00003b74:  00530023  sb(t0, t1, 0)  # [NOC_INDEX (RISC_LOCAL_RAM+0x46)]
  00003b78:  ffb00337  lui(t1, 0xFFB00000)  # t1=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003b7c:  01330313  addi(t1, t1, 0x13)  # t1=BRISC_NOC_MODE (RISC_LOCAL_RAM+0x13)
  00003b80:  00000293  addi(t0, zero, 0)
  00003b84:  00530023  sb(t0, t1, 0)  # [BRISC_NOC_MODE (RISC_LOCAL_RAM+0x13)]
  00003b88:  00001337  lui(t1, 0x1000)  # t1=STREAM_STRIDE (L1+0x1000)
  00003b8c:  94030313  addi(t1, t1, -1728)  # t1=CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)
  00003b90:  00034283  lbu(t0, t1, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)]
  00003b94:  ffb00337  lui(t1, 0xFFB00000)  # t1=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003b98:  04530313  addi(t1, t1, 0x45)  # t1=MY_LOGICAL_X (RISC_LOCAL_RAM+0x45)
  00003b9c:  00530023  sb(t0, t1, 0)  # [MY_LOGICAL_X (RISC_LOCAL_RAM+0x45)]
  00003ba0:  00001337  lui(t1, 0x1000)  # t1=STREAM_STRIDE (L1+0x1000)
  00003ba4:  94130313  addi(t1, t1, -1727)  # t1=CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)
  00003ba8:  00034283  lbu(t0, t1, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)]
  00003bac:  ffb00337  lui(t1, 0xFFB00000)  # t1=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003bb0:  04430313  addi(t1, t1, 0x44)  # t1=MY_LOGICAL_Y (RISC_LOCAL_RAM+0x44)
  00003bb4:  00530023  sb(t0, t1, 0)  # [MY_LOGICAL_Y (RISC_LOCAL_RAM+0x44)]
  00003bb8:  06000313  addi(t1, zero, 0x60)
  00003bbc:  00000293  addi(t0, zero, 0)
  00003bc0:  00532023  sw(t0, t1, 0)
  00003bc4:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00003bc8:  14838393  addi(t2, t2, 0x148)  # t2=NOC_CFG_BASE+0x48 (NOC0+0x148)
  00003bcc:  0003a283  lw(t0, t2, 0)  # [NOC_CFG_BASE+0x48 (NOC0+0x148)]
  00003bd0:  03f2f313  andi(t1, t0, 0x3F)
  00003bd4:  0062d293  srli(t0, t0, 6)
  00003bd8:  03f2f293  andi(t0, t0, 0x3F)
  00003bdc:  00629293  slli(t0, t0, 6)
  00003be0:  00536333  or(t1, t1, t0)
  00003be4:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00003be8:  00438393  addi(t2, t2, 4)  # t2=NOC_TARG_ADDR_MID (NOC0+0x4)
  00003bec:  00000e13  addi(t3, zero, 0)
  00003bf0:  01c3a023  sw(t3, t2, 0)  # [NOC_TARG_ADDR_MID (NOC0+0x4)]
  00003bf4:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00003bf8:  00838393  addi(t2, t2, 8)  # t2=NOC_TARG_ADDR_COORDINATE (NOC0+0x8)
  00003bfc:  0063a023  sw(t1, t2, 0)  # [NOC_TARG_ADDR_COORDINATE (NOC0+0x8)]
  00003c00:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00003c04:  00438393  addi(t2, t2, 4)  # t2=NOC0+0x1004
  00003c08:  00000e13  addi(t3, zero, 0)
  00003c0c:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x1004]
  00003c10:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00003c14:  00838393  addi(t2, t2, 8)  # t2=NOC0+0x1008
  00003c18:  0063a023  sw(t1, t2, 0)  # [NOC0+0x1008]
  00003c1c:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  00003c20:  80c38393  addi(t2, t2, -2036)  # t2=NOC0+0x180c
  00003c24:  00400e13  addi(t3, zero, 4)
  00003c28:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x180c]
  00003c2c:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  00003c30:  81038393  addi(t2, t2, -2032)  # t2=NOC0+0x1810
  00003c34:  00000e13  addi(t3, zero, 0)
  00003c38:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x1810]
  00003c3c:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  00003c40:  81438393  addi(t2, t2, -2028)  # t2=NOC0+0x1814
  00003c44:  0063a023  sw(t1, t2, 0)  # [NOC0+0x1814]
  00003c48:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00003c4c:  81c38393  addi(t2, t2, -2020)  # t2=NOC0+0x81c
  00003c50:  00002e37  lui(t3, 0x2000)  # t3=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  00003c54:  090e0e13  addi(t3, t3, 0x90)  # t3=NOC_CMD_RD_FIELD (L1+0x2090)
  00003c58:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x81c], value=NOC_CMD_RD_FIELD (L1+0x2090)
  00003c5c:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00003c60:  81038393  addi(t2, t2, -2032)  # t2=NOC0+0x810
  00003c64:  00000e13  addi(t3, zero, 0)
  00003c68:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x810]
  00003c6c:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00003c70:  81438393  addi(t2, t2, -2028)  # t2=NOC0+0x814
  00003c74:  0063a023  sw(t1, t2, 0)  # [NOC0+0x814]
  00003c78:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  00003c7c:  14838393  addi(t2, t2, 0x148)  # t2=NOC1+0x148
  00003c80:  0003a283  lw(t0, t2, 0)  # [NOC1+0x148]
  00003c84:  03f2f313  andi(t1, t0, 0x3F)
  00003c88:  0062d293  srli(t0, t0, 6)
  00003c8c:  03f2f293  andi(t0, t0, 0x3F)
  00003c90:  00629293  slli(t0, t0, 6)
  00003c94:  00536333  or(t1, t1, t0)
  00003c98:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  00003c9c:  00438393  addi(t2, t2, 4)  # t2=NOC1+0x4
  00003ca0:  00000e13  addi(t3, zero, 0)
  00003ca4:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x4]
  00003ca8:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  00003cac:  00838393  addi(t2, t2, 8)  # t2=NOC1+0x8
  00003cb0:  0063a023  sw(t1, t2, 0)  # [NOC1+0x8]
  00003cb4:  ffb313b7  lui(t2, 0xFFB31000)  # t2=NOC1+0x1000
  00003cb8:  00438393  addi(t2, t2, 4)  # t2=NOC1+0x1004
  00003cbc:  00000e13  addi(t3, zero, 0)
  00003cc0:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x1004]
  00003cc4:  ffb313b7  lui(t2, 0xFFB31000)  # t2=NOC1+0x1000
  00003cc8:  00838393  addi(t2, t2, 8)  # t2=NOC1+0x1008
  00003ccc:  0063a023  sw(t1, t2, 0)  # [NOC1+0x1008]
  00003cd0:  ffb323b7  lui(t2, 0xFFB32000)  # t2=NOC1+0x2000
  00003cd4:  80c38393  addi(t2, t2, -2036)  # t2=NOC1+0x180c
  00003cd8:  00400e13  addi(t3, zero, 4)
  00003cdc:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x180c]
  00003ce0:  ffb323b7  lui(t2, 0xFFB32000)  # t2=NOC1+0x2000
  00003ce4:  81038393  addi(t2, t2, -2032)  # t2=NOC1+0x1810
  00003ce8:  00000e13  addi(t3, zero, 0)
  00003cec:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x1810]
  00003cf0:  ffb323b7  lui(t2, 0xFFB32000)  # t2=NOC1+0x2000
  00003cf4:  81438393  addi(t2, t2, -2028)  # t2=NOC1+0x1814
  00003cf8:  0063a023  sw(t1, t2, 0)  # [NOC1+0x1814]
  00003cfc:  ffb313b7  lui(t2, 0xFFB31000)  # t2=NOC1+0x1000
  00003d00:  81c38393  addi(t2, t2, -2020)  # t2=NOC1+0x81c
  00003d04:  00002e37  lui(t3, 0x2000)  # t3=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  00003d08:  090e0e13  addi(t3, t3, 0x90)  # t3=NOC_CMD_RD_FIELD (L1+0x2090)
  00003d0c:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x81c], value=NOC_CMD_RD_FIELD (L1+0x2090)
  00003d10:  ffb313b7  lui(t2, 0xFFB31000)  # t2=NOC1+0x1000
  00003d14:  81038393  addi(t2, t2, -2032)  # t2=NOC1+0x810
  00003d18:  00000e13  addi(t3, zero, 0)
  00003d1c:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x810]
  00003d20:  ffb313b7  lui(t2, 0xFFB31000)  # t2=NOC1+0x1000
  00003d24:  81438393  addi(t2, t2, -2028)  # t2=NOC1+0x814
  00003d28:  0063a023  sw(t1, t2, 0)  # [NOC1+0x814]
  00003d2c:  07000293  addi(t0, zero, 0x70)
  00003d30:  0442c303  lbu(t1, t0, 0x44)
  00003d34:  01031393  slli(t2, t1, 0x10)
  00003d38:  ffb20e37  lui(t3, 0xFFB20000)  # t3=NOC_TARG_ADDR_LO (NOC0)
  00003d3c:  208e0e13  addi(t3, t3, 0x208)  # t3=NOC_STATUS_BASE+0x8 (NOC0+0x208)
  00003d40:  007e0e33  add(t3, t3, t2)
  00003d44:  000e2f03  lw(t5, t3, 0)
  00003d48:  00231e13  slli(t3, t1, 2)
  00003d4c:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003d50:  03ce8e93  addi(t4, t4, 0x3C)  # t4=NOC_READS_NUM_ISSUED (RISC_LOCAL_RAM+0x3c)
  00003d54:  01ce8eb3  add(t4, t4, t3)
  00003d58:  01eea023  sw(t5, t4, 0)
  00003d5c:  ffb20e37  lui(t3, 0xFFB20000)  # t3=NOC_TARG_ADDR_LO (NOC0)
  00003d60:  228e0e13  addi(t3, t3, 0x228)  # t3=NOC_STATUS_BASE+0x28 (NOC0+0x228)
  00003d64:  007e0e33  add(t3, t3, t2)
  00003d68:  000e2f03  lw(t5, t3, 0)
  00003d6c:  00231e13  slli(t3, t1, 2)
  00003d70:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003d74:  034e8e93  addi(t4, t4, 0x34)  # t4=CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x34)
  00003d78:  01ce8eb3  add(t4, t4, t3)
  00003d7c:  01eea023  sw(t5, t4, 0)
  00003d80:  ffb20e37  lui(t3, 0xFFB20000)  # t3=NOC_TARG_ADDR_LO (NOC0)
  00003d84:  204e0e13  addi(t3, t3, 0x204)  # t3=NOC_STATUS_BASE+0x4 (NOC0+0x204)
  00003d88:  007e0e33  add(t3, t3, t2)
  00003d8c:  000e2f03  lw(t5, t3, 0)
  00003d90:  00231e13  slli(t3, t1, 2)
  00003d94:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003d98:  02ce8e93  addi(t4, t4, 0x2C)  # t4=NOC_NONPOSTED_WRITES_ACKED (RISC_LOCAL_RAM+0x2c)
  00003d9c:  01ce8eb3  add(t4, t4, t3)
  00003da0:  01eea023  sw(t5, t4, 0)
  00003da4:  ffb20e37  lui(t3, 0xFFB20000)  # t3=NOC_TARG_ADDR_LO (NOC0)
  00003da8:  200e0e13  addi(t3, t3, 0x200)  # t3=NOC_STATUS_BASE (NOC0+0x200)
  00003dac:  007e0e33  add(t3, t3, t2)
  00003db0:  000e2f03  lw(t5, t3, 0)
  00003db4:  00231e13  slli(t3, t1, 2)
  00003db8:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003dbc:  024e8e93  addi(t4, t4, 0x24)  # t4=NOC_NONPOSTED_ATOMICS_ACKED (RISC_LOCAL_RAM+0x24)
  00003dc0:  01ce8eb3  add(t4, t4, t3)
  00003dc4:  01eea023  sw(t5, t4, 0)
  00003dc8:  ffb20e37  lui(t3, 0xFFB20000)  # t3=NOC_TARG_ADDR_LO (NOC0)
  00003dcc:  22ce0e13  addi(t3, t3, 0x22C)  # t3=NOC_STATUS_BASE+0x2c (NOC0+0x22c)
  00003dd0:  007e0e33  add(t3, t3, t2)
  00003dd4:  000e2f03  lw(t5, t3, 0)
  00003dd8:  00231e13  slli(t3, t1, 2)
  00003ddc:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003de0:  01ce8e93  addi(t4, t4, 0x1C)  # t4=NOC_POSTED_WRITES_NUM_ISSUED (RISC_LOCAL_RAM+0x1c)
  00003de4:  01ce8eb3  add(t4, t4, t3)
  00003de8:  01eea023  sw(t5, t4, 0)
  00003dec:  06900293  addi(t0, zero, 0x69)
  00003df0:  00300313  addi(t1, zero, 3)
  00003df4:  00628023  sb(t1, t0, 0)
run_loop:
  00003df8:  37300293  addi(t0, zero, 0x373)
.Lwait_go_17:
  00003dfc:  0002c303  lbu(t1, t0, 0)
  00003e00:  08000393  addi(t2, zero, 0x80)
  00003e04:  14730463  beq(t1, t2, .Lgo_seen_22)  # beq(t1, t2, 0x148)
  00003e08:  0c000393  addi(t2, zero, 0xC0)
  00003e0c:  00730e63  beq(t1, t2, .Lreset_launch_ptr_notify_21)  # beq(t1, t2, 0x1C)
.Lcheck_reset_host_18:
  00003e10:  0e000393  addi(t2, zero, 0xE0)
  00003e14:  12730063  beq(t1, t2, .Lreset_launch_ptr_20)  # beq(t1, t2, 0x120)
.Lcheck_replay_19:
  00003e18:  0f000393  addi(t2, zero, 0xF0)
  00003e1c:  00730663  beq(t1, t2, .Lreset_launch_ptr_notify_21)  # beq(t1, t2, 0xC)
  00003e20:  0ff0000f  fence()
  00003e24:  fd9ff06f  jal(zero, .Lwait_go_17)  # jal(zero, -40)
.Lreset_launch_ptr_notify_21:
  00003e28:  06c00293  addi(t0, zero, 0x6C)
  00003e2c:  00000393  addi(t2, zero, 0)
  00003e30:  0072a023  sw(t2, t0, 0)
  00003e34:  37300293  addi(t0, zero, 0x373)
  00003e38:  00000313  addi(t1, zero, 0)
  00003e3c:  00628023  sb(t1, t0, 0)
  00003e40:  07000293  addi(t0, zero, 0x70)
  00003e44:  02a2c303  lbu(t1, t0, 0x2A)
  00003e48:  00000f13  addi(t5, zero, 0)
  00003e4c:  0de31e63  bne(t1, t5, .Lskip_dispatch_notify_23)  # bne(t1, t5, 0xDC)
  00003e50:  37000e13  addi(t3, zero, 0x370)
  00003e54:  000e4e83  lbu(t4, t3, 0)
  00003e58:  00ce9e93  slli(t4, t4, 0xC)
  00003e5c:  ffb70f37  lui(t5, 0xFFB70000)  # t5=STREAM_REGS+0x30000
  00003e60:  438f0f13  addi(t5, t5, 0x438)  # t5=DISPATCH_MESSAGE_ADDR (STREAM_REGS+0x30438)
  00003e64:  01ee8eb3  add(t4, t4, t5)
  00003e68:  002e4f03  lbu(t5, t3, 2)
  00003e6c:  006f1f13  slli(t5, t5, 6)
  00003e70:  001e4303  lbu(t1, t3, 1)
  00003e74:  006f6f33  or(t5, t5, t1)
  00003e78:  00000f93  addi(t6, zero, 0)
  00003e7c:  0442cf83  lbu(t6, t0, 0x44)
  00003e80:  010f9f93  slli(t6, t6, 0x10)
  00003e84:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  00003e88:  840e0e13  addi(t3, t3, -1984)  # t3=NOC0+0x1840
  00003e8c:  01fe0e33  add(t3, t3, t6)
.Lwait_noc_cmd_buf_24:
  00003e90:  000e2303  lw(t1, t3, 0)
  00003e94:  fe031ee3  bne(t1, zero, .Lwait_noc_cmd_buf_24)  # bne(t1, zero, -4)
  00003e98:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  00003e9c:  828e0e13  addi(t3, t3, -2008)  # t3=NOC0+0x1828
  00003ea0:  01fe0e33  add(t3, t3, t6)
  00003ea4:  04000313  addi(t1, zero, 0x40)
  00003ea8:  006e2023  sw(t1, t3, 0)
  00003eac:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  00003eb0:  81ce0e13  addi(t3, t3, -2020)  # t3=NOC0+0x181c
  00003eb4:  01fe0e33  add(t3, t3, t6)
  00003eb8:  00002337  lui(t1, 0x2000)  # t1=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  00003ebc:  08a30313  addi(t1, t1, 0x8A)  # t1=NOC_INLINE_WRITE_POSTED_FIELD (L1+0x208a)
  00003ec0:  006e2023  sw(t1, t3, 0)  # value=NOC_INLINE_WRITE_POSTED_FIELD (L1+0x208a)
  00003ec4:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  00003ec8:  800e0e13  addi(t3, t3, -2048)  # t3=NOC0+0x1800
  00003ecc:  01fe0e33  add(t3, t3, t6)
  00003ed0:  01de2023  sw(t4, t3, 0)
  00003ed4:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  00003ed8:  804e0e13  addi(t3, t3, -2044)  # t3=NOC0+0x1804
  00003edc:  01fe0e33  add(t3, t3, t6)
  00003ee0:  00000313  addi(t1, zero, 0)
  00003ee4:  006e2023  sw(t1, t3, 0)
  00003ee8:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  00003eec:  808e0e13  addi(t3, t3, -2040)  # t3=NOC0+0x1808
  00003ef0:  01fe0e33  add(t3, t3, t6)
  00003ef4:  01ee2023  sw(t5, t3, 0)
  00003ef8:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  00003efc:  820e0e13  addi(t3, t3, -2016)  # t3=NOC0+0x1820
  00003f00:  01fe0e33  add(t3, t3, t6)
  00003f04:  00f00313  addi(t1, zero, 0xF)
  00003f08:  006e2023  sw(t1, t3, 0)
  00003f0c:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  00003f10:  840e0e13  addi(t3, t3, -1984)  # t3=NOC0+0x1840
  00003f14:  01fe0e33  add(t3, t3, t6)
  00003f18:  00100313  addi(t1, zero, 1)
  00003f1c:  006e2023  sw(t1, t3, 0)
  00003f20:  0402a623  sw(zero, t0, 0x4C)
  00003f24:  04028fa3  sb(zero, t0, 0x5F)
.Lskip_dispatch_notify_23:
  00003f28:  37300293  addi(t0, zero, 0x373)
  00003f2c:  0ff0000f  fence()
  00003f30:  ecdff06f  jal(zero, .Lwait_go_17)  # jal(zero, -308)
.Lreset_launch_ptr_20:
  00003f34:  06c00293  addi(t0, zero, 0x6C)
  00003f38:  00000393  addi(t2, zero, 0)
  00003f3c:  0072a023  sw(t2, t0, 0)
  00003f40:  37300293  addi(t0, zero, 0x373)
  00003f44:  0ff0000f  fence()
  00003f48:  eb5ff06f  jal(zero, .Lwait_go_17)  # jal(zero, -332)
.Lgo_seen_22:
  00003f4c:  0ff0000f  fence()
  00003f50:  06900293  addi(t0, zero, 0x69)
  00003f54:  00000393  addi(t2, zero, 0)
.Lwait8_25:
  00003f58:  0002c303  lbu(t1, t0, 0)
  00003f5c:  00730663  beq(t1, t2, .Lwait8_done_26)  # beq(t1, t2, 0xC)
  00003f60:  0ff0000f  fence()
  00003f64:  ff5ff06f  jal(zero, .Lwait8_25)  # jal(zero, -12)
.Lwait8_done_26:
  00003f68:  0ff0000f  fence()
  00003f6c:  07000293  addi(t0, zero, 0x70)
  00003f70:  0002a303  lw(t1, t0, 0)
  00003f74:  00c2d383  lhu(t2, t0, 0xC)
  00003f78:  00730e33  add(t3, t1, t2)
  00003f7c:  ffb01eb7  lui(t4, 0xFFB01000)  # t4=TRISC_STACK_TOP+0x10 (RISC_LOCAL_RAM+0x1000)
  00003f80:  86ce8e93  addi(t4, t4, -1940)  # t4=SEM_L1_BASE (RISC_LOCAL_RAM+0x86c)
  00003f84:  01cea023  sw(t3, t4, 0)  # [SEM_L1_BASE (RISC_LOCAL_RAM+0x86c)]
  00003f88:  00e2d383  lhu(t2, t0, 0xE)
  00003f8c:  00730e33  add(t3, t1, t2)
  00003f90:  ffb01eb7  lui(t4, 0xFFB01000)  # t4=TRISC_STACK_TOP+0x10 (RISC_LOCAL_RAM+0x1000)
  00003f94:  870e8e93  addi(t4, t4, -1936)  # t4=SEM_L1_BASE+0x4 (RISC_LOCAL_RAM+0x870)
  00003f98:  01cea023  sw(t3, t4, 0)  # [SEM_L1_BASE+0x4 (RISC_LOCAL_RAM+0x870)]
  00003f9c:  0102d383  lhu(t2, t0, 0x10)
  00003fa0:  00730e33  add(t3, t1, t2)
  00003fa4:  ffb01eb7  lui(t4, 0xFFB01000)  # t4=TRISC_STACK_TOP+0x10 (RISC_LOCAL_RAM+0x1000)
  00003fa8:  874e8e93  addi(t4, t4, -1932)  # t4=SEM_L1_BASE+0x8 (RISC_LOCAL_RAM+0x874)
  00003fac:  01cea023  sw(t3, t4, 0)  # [SEM_L1_BASE+0x8 (RISC_LOCAL_RAM+0x874)]
  00003fb0:  0162d383  lhu(t2, t0, 0x16)
  00003fb4:  00730e33  add(t3, t1, t2)
  00003fb8:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003fbc:  018e8e93  addi(t4, t4, 0x18)  # t4=RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)
  00003fc0:  01cea023  sw(t3, t4, 0)  # [RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)]
  00003fc4:  0182d383  lhu(t2, t0, 0x18)
  00003fc8:  00730e33  add(t3, t1, t2)
  00003fcc:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003fd0:  014e8e93  addi(t4, t4, 0x14)  # t4=CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x14)
  00003fd4:  01cea023  sw(t3, t4, 0)  # [CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x14)]
  00003fd8:  07000293  addi(t0, zero, 0x70)
  00003fdc:  0442c303  lbu(t1, t0, 0x44)
  00003fe0:  00031a63  bne(t1, zero, .Lkeep_launch_noc_27)  # bne(t1, zero, 0x14)
  00003fe4:  04c2a303  lw(t1, t0, 0x4C)
  00003fe8:  00237313  andi(t1, t1, 2)
  00003fec:  00030463  beq(t1, zero, .Lkeep_launch_noc_27)  # beq(t1, zero, 8)
  00003ff0:  00100313  addi(t1, zero, 1)
.Lkeep_launch_noc_27:
  00003ff4:  04628223  sb(t1, t0, 0x44)
  00003ff8:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00003ffc:  04638393  addi(t2, t2, 0x46)  # t2=NOC_INDEX (RISC_LOCAL_RAM+0x46)
  00004000:  00638023  sb(t1, t2, 0)  # [NOC_INDEX (RISC_LOCAL_RAM+0x46)]
  00004004:  0452c303  lbu(t1, t0, 0x45)
  00004008:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  0000400c:  01338393  addi(t2, t2, 0x13)  # t2=BRISC_NOC_MODE (RISC_LOCAL_RAM+0x13)
  00004010:  00638023  sb(t1, t2, 0)  # [BRISC_NOC_MODE (RISC_LOCAL_RAM+0x13)]
  00004014:  000013b7  lui(t2, 0x1000)  # t2=STREAM_STRIDE (L1+0x1000)
  00004018:  94038393  addi(t2, t2, -1728)  # t2=CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)
  0000401c:  0003c303  lbu(t1, t2, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)]
  00004020:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00004024:  04538393  addi(t2, t2, 0x45)  # t2=MY_LOGICAL_X (RISC_LOCAL_RAM+0x45)
  00004028:  00638023  sb(t1, t2, 0)  # [MY_LOGICAL_X (RISC_LOCAL_RAM+0x45)]
  0000402c:  05c2ce03  lbu(t3, t0, 0x5C)
  00004030:  41c30333  sub(t1, t1, t3)
  00004034:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00004038:  01238393  addi(t2, t2, 0x12)  # t2=MY_RELATIVE_X (RISC_LOCAL_RAM+0x12)
  0000403c:  00638023  sb(t1, t2, 0)  # [MY_RELATIVE_X (RISC_LOCAL_RAM+0x12)]
  00004040:  000013b7  lui(t2, 0x1000)  # t2=STREAM_STRIDE (L1+0x1000)
  00004044:  94138393  addi(t2, t2, -1727)  # t2=CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)
  00004048:  0003c303  lbu(t1, t2, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)]
  0000404c:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00004050:  04438393  addi(t2, t2, 0x44)  # t2=MY_LOGICAL_Y (RISC_LOCAL_RAM+0x44)
  00004054:  00638023  sb(t1, t2, 0)  # [MY_LOGICAL_Y (RISC_LOCAL_RAM+0x44)]
  00004058:  05d2ce03  lbu(t3, t0, 0x5D)
  0000405c:  41c30333  sub(t1, t1, t3)
  00004060:  ffb003b7  lui(t2, 0xFFB00000)  # t2=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00004064:  01138393  addi(t2, t2, 0x11)  # t2=MY_RELATIVE_Y (RISC_LOCAL_RAM+0x11)
  00004068:  00638023  sb(t1, t2, 0)  # [MY_RELATIVE_Y (RISC_LOCAL_RAM+0x11)]
  0000406c:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00004070:  14838393  addi(t2, t2, 0x148)  # t2=NOC_CFG_BASE+0x48 (NOC0+0x148)
  00004074:  0003a283  lw(t0, t2, 0)  # [NOC_CFG_BASE+0x48 (NOC0+0x148)]
  00004078:  03f2f313  andi(t1, t0, 0x3F)
  0000407c:  0062d293  srli(t0, t0, 6)
  00004080:  03f2f293  andi(t0, t0, 0x3F)
  00004084:  00629293  slli(t0, t0, 6)
  00004088:  00536333  or(t1, t1, t0)
  0000408c:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00004090:  00438393  addi(t2, t2, 4)  # t2=NOC_TARG_ADDR_MID (NOC0+0x4)
  00004094:  00000e13  addi(t3, zero, 0)
  00004098:  01c3a023  sw(t3, t2, 0)  # [NOC_TARG_ADDR_MID (NOC0+0x4)]
  0000409c:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  000040a0:  00838393  addi(t2, t2, 8)  # t2=NOC_TARG_ADDR_COORDINATE (NOC0+0x8)
  000040a4:  0063a023  sw(t1, t2, 0)  # [NOC_TARG_ADDR_COORDINATE (NOC0+0x8)]
  000040a8:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  000040ac:  00438393  addi(t2, t2, 4)  # t2=NOC0+0x1004
  000040b0:  00000e13  addi(t3, zero, 0)
  000040b4:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x1004]
  000040b8:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  000040bc:  00838393  addi(t2, t2, 8)  # t2=NOC0+0x1008
  000040c0:  0063a023  sw(t1, t2, 0)  # [NOC0+0x1008]
  000040c4:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  000040c8:  80c38393  addi(t2, t2, -2036)  # t2=NOC0+0x180c
  000040cc:  00400e13  addi(t3, zero, 4)
  000040d0:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x180c]
  000040d4:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  000040d8:  81038393  addi(t2, t2, -2032)  # t2=NOC0+0x1810
  000040dc:  00000e13  addi(t3, zero, 0)
  000040e0:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x1810]
  000040e4:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  000040e8:  81438393  addi(t2, t2, -2028)  # t2=NOC0+0x1814
  000040ec:  0063a023  sw(t1, t2, 0)  # [NOC0+0x1814]
  000040f0:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  000040f4:  81c38393  addi(t2, t2, -2020)  # t2=NOC0+0x81c
  000040f8:  00002e37  lui(t3, 0x2000)  # t3=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  000040fc:  090e0e13  addi(t3, t3, 0x90)  # t3=NOC_CMD_RD_FIELD (L1+0x2090)
  00004100:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x81c], value=NOC_CMD_RD_FIELD (L1+0x2090)
  00004104:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00004108:  81038393  addi(t2, t2, -2032)  # t2=NOC0+0x810
  0000410c:  00000e13  addi(t3, zero, 0)
  00004110:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x810]
  00004114:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00004118:  81438393  addi(t2, t2, -2028)  # t2=NOC0+0x814
  0000411c:  0063a023  sw(t1, t2, 0)  # [NOC0+0x814]
  00004120:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  00004124:  14838393  addi(t2, t2, 0x148)  # t2=NOC1+0x148
  00004128:  0003a283  lw(t0, t2, 0)  # [NOC1+0x148]
  0000412c:  03f2f313  andi(t1, t0, 0x3F)
  00004130:  0062d293  srli(t0, t0, 6)
  00004134:  03f2f293  andi(t0, t0, 0x3F)
  00004138:  00629293  slli(t0, t0, 6)
  0000413c:  00536333  or(t1, t1, t0)
  00004140:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  00004144:  00438393  addi(t2, t2, 4)  # t2=NOC1+0x4
  00004148:  00000e13  addi(t3, zero, 0)
  0000414c:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x4]
  00004150:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  00004154:  00838393  addi(t2, t2, 8)  # t2=NOC1+0x8
  00004158:  0063a023  sw(t1, t2, 0)  # [NOC1+0x8]
  0000415c:  ffb313b7  lui(t2, 0xFFB31000)  # t2=NOC1+0x1000
  00004160:  00438393  addi(t2, t2, 4)  # t2=NOC1+0x1004
  00004164:  00000e13  addi(t3, zero, 0)
  00004168:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x1004]
  0000416c:  ffb313b7  lui(t2, 0xFFB31000)  # t2=NOC1+0x1000
  00004170:  00838393  addi(t2, t2, 8)  # t2=NOC1+0x1008
  00004174:  0063a023  sw(t1, t2, 0)  # [NOC1+0x1008]
  00004178:  ffb323b7  lui(t2, 0xFFB32000)  # t2=NOC1+0x2000
  0000417c:  80c38393  addi(t2, t2, -2036)  # t2=NOC1+0x180c
  00004180:  00400e13  addi(t3, zero, 4)
  00004184:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x180c]
  00004188:  ffb323b7  lui(t2, 0xFFB32000)  # t2=NOC1+0x2000
  0000418c:  81038393  addi(t2, t2, -2032)  # t2=NOC1+0x1810
  00004190:  00000e13  addi(t3, zero, 0)
  00004194:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x1810]
  00004198:  ffb323b7  lui(t2, 0xFFB32000)  # t2=NOC1+0x2000
  0000419c:  81438393  addi(t2, t2, -2028)  # t2=NOC1+0x1814
  000041a0:  0063a023  sw(t1, t2, 0)  # [NOC1+0x1814]
  000041a4:  ffb313b7  lui(t2, 0xFFB31000)  # t2=NOC1+0x1000
  000041a8:  81c38393  addi(t2, t2, -2020)  # t2=NOC1+0x81c
  000041ac:  00002e37  lui(t3, 0x2000)  # t3=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  000041b0:  090e0e13  addi(t3, t3, 0x90)  # t3=NOC_CMD_RD_FIELD (L1+0x2090)
  000041b4:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x81c], value=NOC_CMD_RD_FIELD (L1+0x2090)
  000041b8:  ffb313b7  lui(t2, 0xFFB31000)  # t2=NOC1+0x1000
  000041bc:  81038393  addi(t2, t2, -2032)  # t2=NOC1+0x810
  000041c0:  00000e13  addi(t3, zero, 0)
  000041c4:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x810]
  000041c8:  ffb313b7  lui(t2, 0xFFB31000)  # t2=NOC1+0x1000
  000041cc:  81438393  addi(t2, t2, -2028)  # t2=NOC1+0x814
  000041d0:  0063a023  sw(t1, t2, 0)  # [NOC1+0x814]
  000041d4:  07000293  addi(t0, zero, 0x70)
  000041d8:  0442c303  lbu(t1, t0, 0x44)
  000041dc:  01031393  slli(t2, t1, 0x10)
  000041e0:  ffb20e37  lui(t3, 0xFFB20000)  # t3=NOC_TARG_ADDR_LO (NOC0)
  000041e4:  208e0e13  addi(t3, t3, 0x208)  # t3=NOC_STATUS_BASE+0x8 (NOC0+0x208)
  000041e8:  007e0e33  add(t3, t3, t2)
  000041ec:  000e2f03  lw(t5, t3, 0)
  000041f0:  00231e13  slli(t3, t1, 2)
  000041f4:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000041f8:  03ce8e93  addi(t4, t4, 0x3C)  # t4=NOC_READS_NUM_ISSUED (RISC_LOCAL_RAM+0x3c)
  000041fc:  01ce8eb3  add(t4, t4, t3)
  00004200:  01eea023  sw(t5, t4, 0)
  00004204:  ffb20e37  lui(t3, 0xFFB20000)  # t3=NOC_TARG_ADDR_LO (NOC0)
  00004208:  228e0e13  addi(t3, t3, 0x228)  # t3=NOC_STATUS_BASE+0x28 (NOC0+0x228)
  0000420c:  007e0e33  add(t3, t3, t2)
  00004210:  000e2f03  lw(t5, t3, 0)
  00004214:  00231e13  slli(t3, t1, 2)
  00004218:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  0000421c:  034e8e93  addi(t4, t4, 0x34)  # t4=CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x34)
  00004220:  01ce8eb3  add(t4, t4, t3)
  00004224:  01eea023  sw(t5, t4, 0)
  00004228:  ffb20e37  lui(t3, 0xFFB20000)  # t3=NOC_TARG_ADDR_LO (NOC0)
  0000422c:  204e0e13  addi(t3, t3, 0x204)  # t3=NOC_STATUS_BASE+0x4 (NOC0+0x204)
  00004230:  007e0e33  add(t3, t3, t2)
  00004234:  000e2f03  lw(t5, t3, 0)
  00004238:  00231e13  slli(t3, t1, 2)
  0000423c:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00004240:  02ce8e93  addi(t4, t4, 0x2C)  # t4=NOC_NONPOSTED_WRITES_ACKED (RISC_LOCAL_RAM+0x2c)
  00004244:  01ce8eb3  add(t4, t4, t3)
  00004248:  01eea023  sw(t5, t4, 0)
  0000424c:  ffb20e37  lui(t3, 0xFFB20000)  # t3=NOC_TARG_ADDR_LO (NOC0)
  00004250:  200e0e13  addi(t3, t3, 0x200)  # t3=NOC_STATUS_BASE (NOC0+0x200)
  00004254:  007e0e33  add(t3, t3, t2)
  00004258:  000e2f03  lw(t5, t3, 0)
  0000425c:  00231e13  slli(t3, t1, 2)
  00004260:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00004264:  024e8e93  addi(t4, t4, 0x24)  # t4=NOC_NONPOSTED_ATOMICS_ACKED (RISC_LOCAL_RAM+0x24)
  00004268:  01ce8eb3  add(t4, t4, t3)
  0000426c:  01eea023  sw(t5, t4, 0)
  00004270:  ffb20e37  lui(t3, 0xFFB20000)  # t3=NOC_TARG_ADDR_LO (NOC0)
  00004274:  22ce0e13  addi(t3, t3, 0x22C)  # t3=NOC_STATUS_BASE+0x2c (NOC0+0x22c)
  00004278:  007e0e33  add(t3, t3, t2)
  0000427c:  000e2f03  lw(t5, t3, 0)
  00004280:  00231e13  slli(t3, t1, 2)
  00004284:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00004288:  01ce8e93  addi(t4, t4, 0x1C)  # t4=NOC_POSTED_WRITES_NUM_ISSUED (RISC_LOCAL_RAM+0x1c)
  0000428c:  01ce8eb3  add(t4, t4, t3)
  00004290:  01eea023  sw(t5, t4, 0)
  00004294:  ffef02b7  lui(t0, 0xFFEF0000)  # t0=TENSIX_CFG_BASE (TENSIX_CFG)
  00004298:  2e428293  addi(t0, t0, 0x2E4)  # t0=RISCV_IC_INVALIDATE_INVALIDATE_ALL (TENSIX_CFG+0x2e4)
  0000429c:  01f00313  addi(t1, zero, 0x1F)
  000042a0:  0062a023  sw(t1, t0, 0)  # [RISCV_IC_INVALIDATE_INVALIDATE_ALL (TENSIX_CFG+0x2e4)]
  000042a4:  07000293  addi(t0, zero, 0x70)
  000042a8:  04c2a283  lw(t0, t0, 0x4C)
  000042ac:  00200313  addi(t1, zero, 2)
  000042b0:  0062f2b3  and(t0, t0, t1)
  000042b4:  00028863  beq(t0, zero, .Lskip_subordinate_signal_28)  # beq(t0, zero, 0x10)
  000042b8:  06800293  addi(t0, zero, 0x68)
  000042bc:  00100313  addi(t1, zero, 1)
  000042c0:  00628023  sb(t1, t0, 0)
.Lskip_subordinate_signal_28:
  000042c4:  07000293  addi(t0, zero, 0x70)
  000042c8:  04c2a283  lw(t0, t0, 0x4C)
  000042cc:  00400313  addi(t1, zero, 4)
  000042d0:  0062f2b3  and(t0, t0, t1)
  000042d4:  00028863  beq(t0, zero, .Lskip_subordinate_signal_29)  # beq(t0, zero, 0x10)
  000042d8:  06900293  addi(t0, zero, 0x69)
  000042dc:  08000313  addi(t1, zero, 0x80)
  000042e0:  00628023  sb(t1, t0, 0)
.Lskip_subordinate_signal_29:
  000042e4:  07000293  addi(t0, zero, 0x70)
  000042e8:  04c2a283  lw(t0, t0, 0x4C)
  000042ec:  00800313  addi(t1, zero, 8)
  000042f0:  0062f2b3  and(t0, t0, t1)
  000042f4:  00028863  beq(t0, zero, .Lskip_subordinate_signal_30)  # beq(t0, zero, 0x10)
  000042f8:  06a00293  addi(t0, zero, 0x6A)
  000042fc:  08000313  addi(t1, zero, 0x80)
  00004300:  00628023  sb(t1, t0, 0)
.Lskip_subordinate_signal_30:
  00004304:  07000293  addi(t0, zero, 0x70)
  00004308:  04c2a283  lw(t0, t0, 0x4C)
  0000430c:  01000313  addi(t1, zero, 0x10)
  00004310:  0062f2b3  and(t0, t0, t1)
  00004314:  00028863  beq(t0, zero, .Lskip_subordinate_signal_31)  # beq(t0, zero, 0x10)
  00004318:  06b00293  addi(t0, zero, 0x6B)
  0000431c:  08000313  addi(t1, zero, 0x80)
  00004320:  00628023  sb(t1, t0, 0)
.Lskip_subordinate_signal_31:
  00004324:  07000293  addi(t0, zero, 0x70)
  00004328:  0002a303  lw(t1, t0, 0)
  0000432c:  0122d383  lhu(t2, t0, 0x12)
  00004330:  007303b3  add(t2, t1, t2)
  00004334:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00004338:  048e0e13  addi(t3, t3, 0x48)  # t3=CB_INTERFACE (RISC_LOCAL_RAM+0x48)
  0000433c:  0402ae83  lw(t4, t0, 0x40)
  00004340:  ffb482b7  lui(t0, 0xFFB48000)  # t0=STREAM_REGS+0x8000
  00004344:  02028293  addi(t0, t0, 0x20)  # t0=CB_SYNC_TILES_ACKED_BASE (STREAM_REGS+0x8020)
  00004348:  ffb48337  lui(t1, 0xFFB48000)  # t1=STREAM_REGS+0x8000
  0000434c:  02830313  addi(t1, t1, 0x28)  # t1=CB_SYNC_TILES_RECEIVED_BASE (STREAM_REGS+0x8028)
.Lsetup_cb_32:
  00004350:  060e8263  beq(t4, zero, .Ldone_cb_34)  # beq(t4, zero, 0x64)
  00004354:  001eff13  andi(t5, t4, 1)
  00004358:  040f0063  beq(t5, zero, .Lskip_cb_33)  # beq(t5, zero, 0x40)
  0000435c:  0043af03  lw(t5, t2, 4)
  00004360:  0003af83  lw(t6, t2, 0)
  00004364:  01ee2023  sw(t5, t3, 0)  # [CB_INTERFACE (RISC_LOCAL_RAM+0x48)]
  00004368:  01ef8f33  add(t5, t6, t5)
  0000436c:  01ee2223  sw(t5, t3, 4)  # [CB_INTERFACE+0x4 (RISC_LOCAL_RAM+0x4c)]
  00004370:  00c3af03  lw(t5, t2, 0xC)
  00004374:  01ee2423  sw(t5, t3, 8)  # [CB_INTERFACE+0x8 (RISC_LOCAL_RAM+0x50)]
  00004378:  0083af03  lw(t5, t2, 8)
  0000437c:  01ee2623  sw(t5, t3, 0xC)  # [CB_INTERFACE+0xc (RISC_LOCAL_RAM+0x54)]
  00004380:  01fe2823  sw(t6, t3, 0x10)  # [CB_INTERFACE+0x10 (RISC_LOCAL_RAM+0x58)]
  00004384:  01fe2a23  sw(t6, t3, 0x14)  # [L1_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x5c)]
  00004388:  000e2c23  sw(zero, t3, 0x18)  # [L1_BANK_TO_NOC_XY+0x4 (RISC_LOCAL_RAM+0x60)]
  0000438c:  000e2e23  sw(zero, t3, 0x1C)  # [L1_BANK_TO_NOC_XY+0x8 (RISC_LOCAL_RAM+0x64)]
  00004390:  0002a023  sw(zero, t0, 0)  # [CB_SYNC_TILES_ACKED_BASE (STREAM_REGS+0x8020)]
  00004394:  00032023  sw(zero, t1, 0)  # [CB_SYNC_TILES_RECEIVED_BASE (STREAM_REGS+0x8028)]
.Lskip_cb_33:
  00004398:  01038393  addi(t2, t2, 0x10)
  0000439c:  020e0e13  addi(t3, t3, 0x20)  # t3=L1_BANK_TO_NOC_XY+0xc (RISC_LOCAL_RAM+0x68)
  000043a0:  00001f37  lui(t5, 0x1000)  # t5=STREAM_STRIDE (L1+0x1000)
  000043a4:  01e282b3  add(t0, t0, t5)
  000043a8:  01e30333  add(t1, t1, t5)
  000043ac:  001ede93  srli(t4, t4, 1)
  000043b0:  fa1ff06f  jal(zero, .Lsetup_cb_32)  # jal(zero, -96)
.Ldone_cb_34:
  000043b4:  07000293  addi(t0, zero, 0x70)
  000043b8:  04c2a283  lw(t0, t0, 0x4C)
  000043bc:  00200313  addi(t1, zero, 2)
  000043c0:  0062f2b3  and(t0, t0, t1)
  000043c4:  00028863  beq(t0, zero, .Lskip_subordinate_signal_35)  # beq(t0, zero, 0x10)
  000043c8:  06800293  addi(t0, zero, 0x68)
  000043cc:  08000313  addi(t1, zero, 0x80)
  000043d0:  00628023  sb(t1, t0, 0)
.Lskip_subordinate_signal_35:
  000043d4:  07000e93  addi(t4, zero, 0x70)
  000043d8:  04ceae83  lw(t4, t4, 0x4C)
  000043dc:  00100393  addi(t2, zero, 1)
  000043e0:  007efeb3  and(t4, t4, t2)
  000043e4:  000e8c63  beq(t4, zero, .Lskip_kernel_36)  # beq(t4, zero, 0x18)
  000043e8:  07000293  addi(t0, zero, 0x70)
  000043ec:  0002a303  lw(t1, t0, 0)
  000043f0:  02c2a383  lw(t2, t0, 0x2C)
  000043f4:  00730e33  add(t3, t1, t2)
  000043f8:  000e00e7  jalr(ra, t3)
.Lskip_kernel_36:
  000043fc:  06800293  addi(t0, zero, 0x68)
  00004400:  00000393  addi(t2, zero, 0)
.Lwait8_37:
  00004404:  0002c303  lbu(t1, t0, 0)
  00004408:  00730663  beq(t1, t2, .Lwait8_done_38)  # beq(t1, t2, 0xC)
  0000440c:  0ff0000f  fence()
  00004410:  ff5ff06f  jal(zero, .Lwait8_37)  # jal(zero, -12)
.Lwait8_done_38:
  00004414:  0ff0000f  fence()
  00004418:  06900293  addi(t0, zero, 0x69)
  0000441c:  00000393  addi(t2, zero, 0)
.Lwait8_39:
  00004420:  0002c303  lbu(t1, t0, 0)
  00004424:  00730663  beq(t1, t2, .Lwait8_done_40)  # beq(t1, t2, 0xC)
  00004428:  0ff0000f  fence()
  0000442c:  ff5ff06f  jal(zero, .Lwait8_39)  # jal(zero, -12)
.Lwait8_done_40:
  00004430:  0ff0000f  fence()
  00004434:  06a00293  addi(t0, zero, 0x6A)
  00004438:  00000393  addi(t2, zero, 0)
.Lwait8_41:
  0000443c:  0002c303  lbu(t1, t0, 0)
  00004440:  00730663  beq(t1, t2, .Lwait8_done_42)  # beq(t1, t2, 0xC)
  00004444:  0ff0000f  fence()
  00004448:  ff5ff06f  jal(zero, .Lwait8_41)  # jal(zero, -12)
.Lwait8_done_42:
  0000444c:  0ff0000f  fence()
  00004450:  06b00293  addi(t0, zero, 0x6B)
  00004454:  00000393  addi(t2, zero, 0)
.Lwait8_43:
  00004458:  0002c303  lbu(t1, t0, 0)
  0000445c:  00730663  beq(t1, t2, .Lwait8_done_44)  # beq(t1, t2, 0xC)
  00004460:  0ff0000f  fence()
  00004464:  ff5ff06f  jal(zero, .Lwait8_43)  # jal(zero, -12)
.Lwait8_done_44:
  00004468:  0ff0000f  fence()
  0000446c:  06900293  addi(t0, zero, 0x69)
  00004470:  00300313  addi(t1, zero, 3)
  00004474:  00628023  sb(t1, t0, 0)
  00004478:  37300293  addi(t0, zero, 0x373)
  0000447c:  00000313  addi(t1, zero, 0)
  00004480:  00628023  sb(t1, t0, 0)
  00004484:  07000293  addi(t0, zero, 0x70)
  00004488:  02a2c303  lbu(t1, t0, 0x2A)
  0000448c:  00000f13  addi(t5, zero, 0)
  00004490:  0de31e63  bne(t1, t5, .Lskip_dispatch_notify_45)  # bne(t1, t5, 0xDC)
  00004494:  37000e13  addi(t3, zero, 0x370)
  00004498:  000e4e83  lbu(t4, t3, 0)
  0000449c:  00ce9e93  slli(t4, t4, 0xC)
  000044a0:  ffb70f37  lui(t5, 0xFFB70000)  # t5=STREAM_REGS+0x30000
  000044a4:  438f0f13  addi(t5, t5, 0x438)  # t5=DISPATCH_MESSAGE_ADDR (STREAM_REGS+0x30438)
  000044a8:  01ee8eb3  add(t4, t4, t5)
  000044ac:  002e4f03  lbu(t5, t3, 2)
  000044b0:  006f1f13  slli(t5, t5, 6)
  000044b4:  001e4303  lbu(t1, t3, 1)
  000044b8:  006f6f33  or(t5, t5, t1)
  000044bc:  00000f93  addi(t6, zero, 0)
  000044c0:  0442cf83  lbu(t6, t0, 0x44)
  000044c4:  010f9f93  slli(t6, t6, 0x10)
  000044c8:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  000044cc:  840e0e13  addi(t3, t3, -1984)  # t3=NOC0+0x1840
  000044d0:  01fe0e33  add(t3, t3, t6)
.Lwait_noc_cmd_buf_46:
  000044d4:  000e2303  lw(t1, t3, 0)
  000044d8:  fe031ee3  bne(t1, zero, .Lwait_noc_cmd_buf_46)  # bne(t1, zero, -4)
  000044dc:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  000044e0:  828e0e13  addi(t3, t3, -2008)  # t3=NOC0+0x1828
  000044e4:  01fe0e33  add(t3, t3, t6)
  000044e8:  04000313  addi(t1, zero, 0x40)
  000044ec:  006e2023  sw(t1, t3, 0)
  000044f0:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  000044f4:  81ce0e13  addi(t3, t3, -2020)  # t3=NOC0+0x181c
  000044f8:  01fe0e33  add(t3, t3, t6)
  000044fc:  00002337  lui(t1, 0x2000)  # t1=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  00004500:  08a30313  addi(t1, t1, 0x8A)  # t1=NOC_INLINE_WRITE_POSTED_FIELD (L1+0x208a)
  00004504:  006e2023  sw(t1, t3, 0)  # value=NOC_INLINE_WRITE_POSTED_FIELD (L1+0x208a)
  00004508:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  0000450c:  800e0e13  addi(t3, t3, -2048)  # t3=NOC0+0x1800
  00004510:  01fe0e33  add(t3, t3, t6)
  00004514:  01de2023  sw(t4, t3, 0)
  00004518:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  0000451c:  804e0e13  addi(t3, t3, -2044)  # t3=NOC0+0x1804
  00004520:  01fe0e33  add(t3, t3, t6)
  00004524:  00000313  addi(t1, zero, 0)
  00004528:  006e2023  sw(t1, t3, 0)
  0000452c:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  00004530:  808e0e13  addi(t3, t3, -2040)  # t3=NOC0+0x1808
  00004534:  01fe0e33  add(t3, t3, t6)
  00004538:  01ee2023  sw(t5, t3, 0)
  0000453c:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  00004540:  820e0e13  addi(t3, t3, -2016)  # t3=NOC0+0x1820
  00004544:  01fe0e33  add(t3, t3, t6)
  00004548:  00f00313  addi(t1, zero, 0xF)
  0000454c:  006e2023  sw(t1, t3, 0)
  00004550:  ffb22e37  lui(t3, 0xFFB22000)  # t3=NOC0+0x2000
  00004554:  840e0e13  addi(t3, t3, -1984)  # t3=NOC0+0x1840
  00004558:  01fe0e33  add(t3, t3, t6)
  0000455c:  00100313  addi(t1, zero, 1)
  00004560:  006e2023  sw(t1, t3, 0)
  00004564:  0402a623  sw(zero, t0, 0x4C)
  00004568:  04028fa3  sb(zero, t0, 0x5F)
.Lskip_dispatch_notify_45:
  0000456c:  06c00313  addi(t1, zero, 0x6C)
  00004570:  00032283  lw(t0, t1, 0)
  00004574:  00128293  addi(t0, t0, 1)
  00004578:  0072f293  andi(t0, t0, 7)
  0000457c:  06c00313  addi(t1, zero, 0x6C)
  00004580:  00532023  sw(t0, t1, 0)
  00004584:  875ff06f  jal(zero, run_loop)  # jal(zero, -1932)
```
