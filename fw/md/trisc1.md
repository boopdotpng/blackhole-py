# trisc1

## Summary

| field | value |
| --- | ---: |
| kind | `trisc1` |
| base | `0x6040` |
| instructions | 120 |
| text bytes | 480 (`0x1e0`) |

## Segments

| label | address | size | flags |
| --- | ---: | ---: | --- |
| `trisc1.text` | `0x6040` | 480 (`0x1e0`) | `RX` |
| `trisc1.local_data` | `0xd2b0` | 28 (`0x1c`) | `RW` |

## Disassembly

```python
; trisc1: blackhole-py firmware

  00006040:  ffb001b7  lui(gp, 0xFFB00000)  # gp=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006044:  7f018193  addi(gp, gp, 0x7F0)  # gp=TRISC_GLOBAL_POINTER (RISC_LOCAL_RAM+0x7f0)
  00006048:  ffb01137  lui(sp, 0xFFB01000)  # sp=TRISC_STACK_TOP+0x10 (RISC_LOCAL_RAM+0x1000)
  0000604c:  ff010113  addi(sp, sp, -16)  # sp=TRISC_STACK_TOP (RISC_LOCAL_RAM+0xff0)
  00006050:  00200293  addi(t0, zero, 2)
  00006054:  7c02a073  csrrs(zero, t0, 0x7C0)
  00006058:  00100293  addi(t0, zero, 1)
  0000605c:  01229293  slli(t0, t0, 0x12)
  00006060:  0ff0000f  fence()
  00006064:  7c02a073  csrrs(zero, t0, 0x7C0)
  00006068:  00200293  addi(t0, zero, 2)
  0000606c:  7c02b073  csrrc(zero, t0, 0x7C0)
  00006070:  0ff0000f  fence()
  00006074:  0ff0000f  fence()
  00006078:  00800293  addi(t0, zero, 8)
  0000607c:  7c02a073  csrrs(zero, t0, 0x7C0)
  00006080:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006084:  0000d337  lui(t1, 0xD000)  # t1=L1+0xd000
  00006088:  2b030313  addi(t1, t1, 0x2B0)  # t1=TensixL1.TRISC1_INIT_LOCAL_L1_BASE_SCRATCH (L1+0xd2b0)
  0000608c:  00700e13  addi(t3, zero, 7)
.Lcopy_words_1:
  00006090:  000e0e63  beq(t3, zero, .Lcopy_done_2)  # beq(t3, zero, 0x1C)
  00006094:  00032383  lw(t2, t1, 0)  # [TensixL1.TRISC1_INIT_LOCAL_L1_BASE_SCRATCH (L1+0xd2b0)]
  00006098:  0072a023  sw(t2, t0, 0)  # [LOCAL_RAM_START (RISC_LOCAL_RAM)]
  0000609c:  00430313  addi(t1, t1, 4)  # t1=TensixL1.TRISC1_INIT_LOCAL_L1_BASE_SCRATCH+0x4 (L1+0xd2b4)
  000060a0:  00428293  addi(t0, t0, 4)  # t0=MY_Y (RISC_LOCAL_RAM+0x4)
  000060a4:  fffe0e13  addi(t3, t3, -1)
  000060a8:  fe9ff06f  jal(zero, .Lcopy_words_1)  # jal(zero, -24)
.Lcopy_done_2:
  000060ac:  ffe002b7  lui(t0, 0xFFE00000)  # t0=REGFILE_BASE
  000060b0:  04000313  addi(t1, zero, 0x40)
.Lzero_regfile_3:
  000060b4:  00030a63  beq(t1, zero, .Lzero_regfile_done_4)  # beq(t1, zero, 0x14)
  000060b8:  0002a023  sw(zero, t0, 0)  # [REGFILE_BASE]
  000060bc:  00428293  addi(t0, t0, 4)  # t0=REGFILE_BASE+0x4
  000060c0:  fff30313  addi(t1, t1, -1)
  000060c4:  ff1ff06f  jal(zero, .Lzero_regfile_3)  # jal(zero, -16)
.Lzero_regfile_done_4:
  000060c8:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000060cc:  00000313  addi(t1, zero, 0)
  000060d0:  0062a023  sw(t1, t0, 0)  # [LOCAL_RAM_START (RISC_LOCAL_RAM)]
  000060d4:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000060d8:  00428293  addi(t0, t0, 4)  # t0=MY_Y (RISC_LOCAL_RAM+0x4)
  000060dc:  00000313  addi(t1, zero, 0)
  000060e0:  0062a023  sw(t1, t0, 0)  # [MY_Y (RISC_LOCAL_RAM+0x4)]
  000060e4:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000060e8:  01828293  addi(t0, t0, 0x18)  # t0=RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)
  000060ec:  00000313  addi(t1, zero, 0)
  000060f0:  0062a023  sw(t1, t0, 0)  # [RTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x18)]
  000060f4:  ffef02b7  lui(t0, 0xFFEF0000)  # t0=TENSIX_CFG_BASE (TENSIX_CFG)
  000060f8:  2e828293  addi(t0, t0, 0x2E8)  # t0=RISCV_IC_INVALIDATE_INVALIDATE_ALL+0x4 (TENSIX_CFG+0x2e8)
  000060fc:  00000313  addi(t1, zero, 0)
  00006100:  0062a023  sw(t1, t0, 0)  # [RISCV_IC_INVALIDATE_INVALIDATE_ALL+0x4 (TENSIX_CFG+0x2e8)]
  00006104:  25800293  addi(t0, zero, 0x258)
.Lwait_cycles_5:
  00006108:  00028663  beq(t0, zero, .Lwait_cycles_done_6)  # beq(t0, zero, 0xC)
  0000610c:  fff28293  addi(t0, t0, -1)
  00006110:  ff9ff06f  jal(zero, .Lwait_cycles_5)  # jal(zero, -8)
.Lwait_cycles_done_6:
  00006114:  000012b7  lui(t0, 0x1000)  # t0=STREAM_STRIDE (L1+0x1000)
  00006118:  94028293  addi(t0, t0, -1728)  # t0=CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)
  0000611c:  0002c303  lbu(t1, t0, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_X (L1+0x940)]
  00006120:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006124:  01528293  addi(t0, t0, 0x15)  # t0=CRTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x15)
  00006128:  00628023  sb(t1, t0, 0)  # [CRTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x15)]
  0000612c:  000012b7  lui(t0, 0x1000)  # t0=STREAM_STRIDE (L1+0x1000)
  00006130:  94128293  addi(t0, t0, -1727)  # t0=CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)
  00006134:  0002c303  lbu(t1, t0, 0)  # [CORE_INFO_ABSOLUTE_LOGICAL_Y (L1+0x941)]
  00006138:  ffb002b7  lui(t0, 0xFFB00000)  # t0=LOCAL_RAM_START (RISC_LOCAL_RAM)
  0000613c:  01428293  addi(t0, t0, 0x14)  # t0=CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x14)
  00006140:  00628023  sb(t1, t0, 0)  # [CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x14)]
  00006144:  06a00293  addi(t0, zero, 0x6A)
  00006148:  00000313  addi(t1, zero, 0)
  0000614c:  00628023  sb(t1, t0, 0)
run_loop:
  00006150:  06a00293  addi(t0, zero, 0x6A)
.Lwait_trisc_7:
  00006154:  0002c303  lbu(t1, t0, 0)
  00006158:  08000393  addi(t2, zero, 0x80)
  0000615c:  00730663  beq(t1, t2, .Ltrisc_go_8)  # beq(t1, t2, 0xC)
  00006160:  0ff0000f  fence()
  00006164:  ff1ff06f  jal(zero, .Lwait_trisc_7)  # jal(zero, -16)
.Ltrisc_go_8:
  00006168:  0ff0000f  fence()
  0000616c:  07000293  addi(t0, zero, 0x70)
  00006170:  0002a303  lw(t1, t0, 0)
  00006174:  0222d383  lhu(t2, t0, 0x22)
  00006178:  00730e33  add(t3, t1, t2)
  0000617c:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006180:  010e8e93  addi(t4, t4, 0x10)  # t4=MY_X+0x8 (RISC_LOCAL_RAM+0x10)
  00006184:  01cea023  sw(t3, t4, 0)  # [MY_X+0x8 (RISC_LOCAL_RAM+0x10)]
  00006188:  0242d383  lhu(t2, t0, 0x24)
  0000618c:  00730e33  add(t3, t1, t2)
  00006190:  ffb00eb7  lui(t4, 0xFFB00000)  # t4=LOCAL_RAM_START (RISC_LOCAL_RAM)
  00006194:  00ce8e93  addi(t4, t4, 0xC)  # t4=MY_X+0x4 (RISC_LOCAL_RAM+0xc)
  00006198:  01cea023  sw(t3, t4, 0)  # [MY_X+0x4 (RISC_LOCAL_RAM+0xc)]
  0000619c:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000061a0:  015e0e13  addi(t3, t3, 0x15)  # t3=CRTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x15)
  000061a4:  000e4e83  lbu(t4, t3, 0)  # [CRTA_L1_BASE_PTR+0x1 (RISC_LOCAL_RAM+0x15)]
  000061a8:  05c2cf03  lbu(t5, t0, 0x5C)
  000061ac:  41ee8eb3  sub(t4, t4, t5)
  000061b0:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000061b4:  009e0e13  addi(t3, t3, 9)  # t3=MY_X+0x1 (RISC_LOCAL_RAM+0x9)
  000061b8:  01de0023  sb(t4, t3, 0)  # [MY_X+0x1 (RISC_LOCAL_RAM+0x9)]
  000061bc:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000061c0:  014e0e13  addi(t3, t3, 0x14)  # t3=CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x14)
  000061c4:  000e4e83  lbu(t4, t3, 0)  # [CRTA_L1_BASE_PTR (RISC_LOCAL_RAM+0x14)]
  000061c8:  05d2cf03  lbu(t5, t0, 0x5D)
  000061cc:  41ee8eb3  sub(t4, t4, t5)
  000061d0:  ffb00e37  lui(t3, 0xFFB00000)  # t3=LOCAL_RAM_START (RISC_LOCAL_RAM)
  000061d4:  008e0e13  addi(t3, t3, 8)  # t3=MY_X (RISC_LOCAL_RAM+0x8)
  000061d8:  01de0023  sb(t4, t3, 0)  # [MY_X (RISC_LOCAL_RAM+0x8)]
  000061dc:  07000293  addi(t0, zero, 0x70)
  000061e0:  0002a303  lw(t1, t0, 0)
  000061e4:  0382a383  lw(t2, t0, 0x38)
  000061e8:  00730e33  add(t3, t1, t2)
  000061ec:  000e00e7  jalr(ra, t3)
  000061f0:  ffe802b7  lui(t0, 0xFFE80000)
  000061f4:  00428293  addi(t0, t0, 4)  # t0=PC_BUF_SYNC
  000061f8:  00000313  addi(t1, zero, 0)
  000061fc:  0062a023  sw(t1, t0, 0)  # [PC_BUF_SYNC]
  00006200:  ffe802b7  lui(t0, 0xFFE80000)
  00006204:  00428293  addi(t0, t0, 4)  # t0=PC_BUF_SYNC
  00006208:  0002a283  lw(t0, t0, 0)  # [PC_BUF_SYNC]
  0000620c:  00507033  and(zero, zero, t0)
  00006210:  06a00293  addi(t0, zero, 0x6A)
  00006214:  00000313  addi(t1, zero, 0)
  00006218:  00628023  sb(t1, t0, 0)
  0000621c:  f35ff06f  jal(zero, run_loop)  # jal(zero, -204)
```
