# trisc0

## Summary

| field | value |
| --- | ---: |
| kind | `trisc0` |
| base | `0x5a40` |
| instructions | 165 |
| text bytes | 660 (`0x294`) |

## Segments

| label | address | size | flags |
| --- | ---: | ---: | --- |
| `trisc0.text` | `0x5a40` | 660 (`0x294`) | `RX` |
| `trisc0.local_data` | `0xc2b0` | 1056 (`0x420`) | `RW` |

## Disassembly

```python
; trisc0: blackhole-py firmware

  00005a40:  ffb001b7  lui(gp, 0xFFB00000)  # gp=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005a44:  7f018193  addi(gp, gp, 0x7F0)  # gp=TRISC_GLOBAL_POINTER (RISC_LOCAL_RAM+0x7f0)
  00005a48:  ffb01137  lui(sp, 0xFFB01000)  # sp=TRISC_STACK_TOP+0x10 (RISC_LOCAL_RAM+0x1000)
  00005a4c:  ff010113  addi(sp, sp, -16)  # sp=TRISC_STACK_TOP (RISC_LOCAL_RAM+0xff0)
  00005a50:  00200293  addi(t0, zero, 2)
  00005a54:  7c02a073  csrrs(zero, t0, 0x7C0)
  00005a58:  00100293  addi(t0, zero, 1)
  00005a5c:  01229293  slli(t0, t0, 0x12)
  00005a60:  0ff0000f  fence()
  00005a64:  7c02a073  csrrs(zero, t0, 0x7C0)
  00005a68:  00200293  addi(t0, zero, 2)
  00005a6c:  7c02b073  csrrc(zero, t0, 0x7C0)
  00005a70:  0ff0000f  fence()
  00005a74:  0ff0000f  fence()
  00005a78:  00800293  addi(t0, zero, 8)
  00005a7c:  7c02a073  csrrs(zero, t0, 0x7C0)
  00005a80:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005a84:  0000c337  lui(t1, 0xC000)  # t1=L1+0xc000
  00005a88:  2b030313  addi(t1, t1, 0x2B0)  # t1=TensixL1.TRISC0_INIT_LOCAL_L1_BASE_SCRATCH (L1+0xc2b0)
  00005a8c:  10800e13  addi(t3, zero, 0x108)
.Lcopy_words_1:
  00005a90:  000e0e63  beq(t3, zero, .Lcopy_done_2)  # beq(t3, zero, 0x1C)
  00005a94:  00032383  lw(t2, t1, 0)  # [TensixL1.TRISC0_INIT_LOCAL_L1_BASE_SCRATCH (L1+0xc2b0)]
  00005a98:  0072a023  sw(t2, t0, 0)  # [LOCAL_RAM_START (RISC_LOCAL_RAM)]
  00005a9c:  00430313  addi(t1, t1, 4)  # t1=TensixL1.TRISC0_INIT_LOCAL_L1_BASE_SCRATCH+0x4 (L1+0xc2b4)
  00005aa0:  00428293  addi(t0, t0, 4)  # t0=MY_Y (RISC_LOCAL_RAM+0x4)
  00005aa4:  fffe0e13  addi(t3, t3, -1)
  00005aa8:  fe9ff06f  jal(zero, .Lcopy_words_1)  # jal(zero, -24)
.Lcopy_done_2:
  00005aac:  ffe002b7  lui(t0, 0xFFE00000)  # t0=REGFILE_BASE
  00005ab0:  04000313  addi(t1, zero, 0x40)
.Lzero_regfile_3:
  00005ab4:  00030a63  beq(t1, zero, .Lzero_regfile_done_4)  # beq(t1, zero, 0x14)
  00005ab8:  0002a023  sw(zero, t0, 0)  # [REGFILE_BASE]
  00005abc:  00428293  addi(t0, t0, 4)  # t0=REGFILE_BASE+0x4
  00005ac0:  fff30313  addi(t1, t1, -1)
  00005ac4:  ff1ff06f  jal(zero, .Lzero_regfile_3)  # jal(zero, -16)
.Lzero_regfile_done_4:
  00005ac8:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005acc:  00000313  addi(t1, zero, 0)
  00005ad0:  0062a023  sw(t1, t0, 0)  # [LOCAL_RAM_START (RISC_LOCAL_RAM)]
  00005ad4:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005ad8:  00428293  addi(t0, t0, 4)  # t0=MY_Y (RISC_LOCAL_RAM+0x4)
  00005adc:  00000313  addi(t1, zero, 0)
  00005ae0:  0062a023  sw(t1, t0, 0)  # [MY_Y (RISC_LOCAL_RAM+0x4)]
  00005ae4:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005ae8:  01c28293  addi(t0, t0, 0x1C)  # t0=NOC_POSTED_WRITES_NUM_ISSUED (RISC_LOCAL_RAM+0x1c)
  00005aec:  00000313  addi(t1, zero, 0)
  00005af0:  0062a023  sw(t1, t0, 0)  # [NOC_POSTED_WRITES_NUM_ISSUED (RISC_LOCAL_RAM+0x1c)]
  00005af4:  ffef02b7  lui(t0, 0xFFEF0000)  # t0=TENSIX_CFG_BASE (TENSIX_CFG)
  00005af8:  2e828293  addi(t0, t0, 0x2E8)  # t0=RISCV_IC_INVALIDATE_INVALIDATE_ALL+0x4 (TENSIX_CFG+0x2e8)
  00005afc:  00000313  addi(t1, zero, 0)
  00005b00:  0062a023  sw(t1, t0, 0)  # [RISCV_IC_INVALIDATE_INVALIDATE_ALL+0x4 (TENSIX_CFG+0x2e8)]
  00005b04:  25800293  addi(t0, zero, 0x258)
.Lwait_cycles_5:
  00005b08:  00028663  beq(t0, zero, .Lwait_cycles_done_6)  # beq(t0, zero, 0xC)
  00005b0c:  fff28293  addi(t0, t0, -1)
  00005b10:  ff9ff06f  jal(zero, .Lwait_cycles_5)  # jal(zero, -8)
.Lwait_cycles_done_6:
  00005b14:  000012b7  lui(t0, 0x1000)  # t0=STREAM_STRIDE (L1+0x1000)
  00005b18:  94028293  addi(t0, t0, -1728)  # t0=CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)
  00005b1c:  0002c303  lbu(t1, t0, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)]
  00005b20:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005b24:  01928293  addi(t0, t0, 0x19)  # t0=RTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x19)
  00005b28:  00628023  sb(t1, t0, 0)  # [RTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x19)]
  00005b2c:  000012b7  lui(t0, 0x1000)  # t0=STREAM_STRIDE (L1+0x1000)
  00005b30:  94128293  addi(t0, t0, -1727)  # t0=CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)
  00005b34:  0002c303  lbu(t1, t0, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)]
  00005b38:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005b3c:  01828293  addi(t0, t0, 0x18)  # t0=RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)
  00005b40:  00628023  sb(t1, t0, 0)  # [RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)]
  00005b44:  06900293  addi(t0, zero, 0x69)
  00005b48:  00000313  addi(t1, zero, 0)
  00005b4c:  00628023  sb(t1, t0, 0)
run_loop:
  00005b50:  06900293  addi(t0, zero, 0x69)
.Lwait_trisc_7:
  00005b54:  0002c303  lbu(t1, t0, 0)
  00005b58:  08000393  addi(t2, zero, 0x80)
  00005b5c:  04730c63  beq(t1, t2, .Ltrisc_go_8)  # beq(t1, t2, 0x58)
  00005b60:  00300393  addi(t2, zero, 3)
  00005b64:  00730663  beq(t1, t2, .Ltrisc_init_sync_9)  # beq(t1, t2, 0xC)
  00005b68:  0ff0000f  fence()
  00005b6c:  fe9ff06f  jal(zero, .Lwait_trisc_7)  # jal(zero, -24)
.Ltrisc_init_sync_9:
  00005b70:  ffb482b7  lui(t0, 0xFFB48000)  # t0=STREAM_REGS+0x8000
  00005b74:  02828293  addi(t0, t0, 0x28)  # t0=CB_SYNC_TILES_RECEIVED_BASE (STREAM_REGS+0x8028)
  00005b78:  ffb48337  lui(t1, 0xFFB48000)  # t1=STREAM_REGS+0x8000
  00005b7c:  02030313  addi(t1, t1, 0x20)  # t1=CB_SYNC_TILES_ACKED_BASE (STREAM_REGS+0x8020)
  00005b80:  04000393  addi(t2, zero, 0x40)
  00005b84:  00001e37  lui(t3, 0x1000)  # t3=STREAM_STRIDE (L1+0x1000)
.Linit_cb_sync_10:
  00005b88:  00038e63  beq(t2, zero, .Linit_cb_sync_done_11)  # beq(t2, zero, 0x1C)
  00005b8c:  0002a023  sw(zero, t0, 0)  # [CB_SYNC_TILES_RECEIVED_BASE (STREAM_REGS+0x8028)]
  00005b90:  00032023  sw(zero, t1, 0)  # [CB_SYNC_TILES_ACKED_BASE (STREAM_REGS+0x8020)]
  00005b94:  01c282b3  add(t0, t0, t3)
  00005b98:  01c30333  add(t1, t1, t3)
  00005b9c:  fff38393  addi(t2, t2, -1)
  00005ba0:  fe9ff06f  jal(zero, .Linit_cb_sync_10)  # jal(zero, -24)
.Linit_cb_sync_done_11:
  00005ba4:  06900293  addi(t0, zero, 0x69)
  00005ba8:  00000393  addi(t2, zero, 0)
  00005bac:  00728023  sb(t2, t0, 0)
  00005bb0:  fa5ff06f  jal(zero, .Lwait_trisc_7)  # jal(zero, -92)
.Ltrisc_go_8:
  00005bb4:  0ff0000f  fence()
  00005bb8:  07000293  addi(t0, zero, 0x70)
  00005bbc:  0002a303  lw(t1, t0, 0)
  00005bc0:  0122d383  lhu(t2, t0, 0x12)
  00005bc4:  007303b3  add(t2, t1, t2)
  00005bc8:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005bcc:  020e0e13  addi(t3, t3, 0x20)  # t3=NOC_POSTED_WRITES_NUM_ISSUED+0x4 (RISC_LOCAL_RAM+0x20)
  00005bd0:  0402ae83  lw(t4, t0, 0x40)
.Lsetup_cb_12:
  00005bd4:  040e8663  beq(t4, zero, .Ldone_cb_14)  # beq(t4, zero, 0x4C)
  00005bd8:  001ef313  andi(t1, t4, 1)
  00005bdc:  02030a63  beq(t1, zero, .Lskip_cb_13)  # beq(t1, zero, 0x34)
  00005be0:  0043af03  lw(t5, t2, 4)
  00005be4:  0003af83  lw(t6, t2, 0)
  00005be8:  00c3a283  lw(t0, t2, 0xC)
  00005bec:  004f5f13  srli(t5, t5, 4)
  00005bf0:  004fdf93  srli(t6, t6, 4)
  00005bf4:  0042d293  srli(t0, t0, 4)
  00005bf8:  01ee2023  sw(t5, t3, 0)  # [NOC_POSTED_WRITES_NUM_ISSUED+0x4 (RISC_LOCAL_RAM+0x20)]
  00005bfc:  01ef8f33  add(t5, t6, t5)
  00005c00:  01ee2223  sw(t5, t3, 4)  # [NOC_NONPOSTED_ATOMICS_ACKED (RISC_LOCAL_RAM+0x24)]
  00005c04:  005e2423  sw(t0, t3, 8)  # [NOC_NONPOSTED_ATOMICS_ACKED+0x4 (RISC_LOCAL_RAM+0x28)]
  00005c08:  01fe2823  sw(t6, t3, 0x10)  # [MY_X (RISC_LOCAL_RAM+0x30)]
  00005c0c:  000e2c23  sw(zero, t3, 0x18)  # [RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x38)]
.Lskip_cb_13:
  00005c10:  01038393  addi(t2, t2, 0x10)
  00005c14:  020e0e13  addi(t3, t3, 0x20)  # t3=DRAM_BANK_TO_NOC_XY (RISC_LOCAL_RAM+0x40)
  00005c18:  001ede93  srli(t4, t4, 1)
  00005c1c:  fb9ff06f  jal(zero, .Lsetup_cb_12)  # jal(zero, -72)
.Ldone_cb_14:
  00005c20:  07000293  addi(t0, zero, 0x70)
  00005c24:  0002a303  lw(t1, t0, 0)
  00005c28:  01e2d383  lhu(t2, t0, 0x1E)
  00005c2c:  00730e33  add(t3, t1, t2)
  00005c30:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005c34:  014e8e93  addi(t4, t4, 0x14)  # t4=CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x14)
  00005c38:  01cea023  sw(t3, t4, 0)  # [CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x14)]
  00005c3c:  0202d383  lhu(t2, t0, 0x20)
  00005c40:  00730e33  add(t3, t1, t2)
  00005c44:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005c48:  010e8e93  addi(t4, t4, 0x10)  # t4=MY_X+0x8 (RISC_LOCAL_RAM+0x10)
  00005c4c:  01cea023  sw(t3, t4, 0)  # [MY_X+0x8 (RISC_LOCAL_RAM+0x10)]
  00005c50:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005c54:  019e0e13  addi(t3, t3, 0x19)  # t3=RTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x19)
  00005c58:  000e4e83  lbu(t4, t3, 0)  # [RTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x19)]
  00005c5c:  05c2cf03  lbu(t5, t0, 0x5C)
  00005c60:  41ee8eb3  sub(t4, t4, t5)
  00005c64:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005c68:  00de0e13  addi(t3, t3, 0xD)  # t3=MY_X+0x5 (RISC_LOCAL_RAM+0xd)
  00005c6c:  01de0023  sb(t4, t3, 0)  # [MY_X+0x5 (RISC_LOCAL_RAM+0xd)]
  00005c70:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005c74:  018e0e13  addi(t3, t3, 0x18)  # t3=RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)
  00005c78:  000e4e83  lbu(t4, t3, 0)  # [RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)]
  00005c7c:  05d2cf03  lbu(t5, t0, 0x5D)
  00005c80:  41ee8eb3  sub(t4, t4, t5)
  00005c84:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00005c88:  00ce0e13  addi(t3, t3, 0xC)  # t3=MY_X+0x4 (RISC_LOCAL_RAM+0xc)
  00005c8c:  01de0023  sb(t4, t3, 0)  # [MY_X+0x4 (RISC_LOCAL_RAM+0xc)]
  00005c90:  07000293  addi(t0, zero, 0x70)
  00005c94:  0002a303  lw(t1, t0, 0)
  00005c98:  0342a383  lw(t2, t0, 0x34)
  00005c9c:  00730e33  add(t3, t1, t2)
  00005ca0:  000e00e7  jalr(ra, t3)
  00005ca4:  ffe802b7  lui(t0, 0xFFE80000)
  00005ca8:  00428293  addi(t0, t0, 4)  # t0=PC_BUF_SYNC
  00005cac:  00000313  addi(t1, zero, 0)
  00005cb0:  0062a023  sw(t1, t0, 0)  # [PC_BUF_SYNC]
  00005cb4:  ffe802b7  lui(t0, 0xFFE80000)
  00005cb8:  00428293  addi(t0, t0, 4)  # t0=PC_BUF_SYNC
  00005cbc:  0002a283  lw(t0, t0, 0)  # [PC_BUF_SYNC]
  00005cc0:  00507033  and(zero, zero, t0)
  00005cc4:  06900293  addi(t0, zero, 0x69)
  00005cc8:  00000313  addi(t1, zero, 0)
  00005ccc:  00628023  sb(t1, t0, 0)
  00005cd0:  e81ff06f  jal(zero, run_loop)  # jal(zero, -384)
```
