# cq_dispatch

## Summary

| field | value |
| --- | ---: |
| kind | `brisc` |
| base | `0x0` |
| instructions | 814 |
| text bytes | 3256 (`0xcb8`) |

## Segments

| label | address | size | flags |
| --- | ---: | ---: | --- |
| `text` | `0x0` | 3256 (`0xcb8`) | `RX` |

## Disassembly

```python
; cq_dispatch: blackhole-py firmware

  00000000:  ffb02137  lui(sp, 0xFFB02000)  # sp=LOCAL_RAM_END+1 (RISC_LOCAL_RAM_END+1)
  00000004:  ff010113  addi(sp, sp, -16)  # sp=BRISC_STACK_TOP (RISC_LOCAL_RAM+0x1ff0)
  00000008:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  0000000c:  c1d10337  lui(t1, 0xC1D10000)
  00000010:  00130313  addi(t1, t1, 1)
  00000014:  0062a023  sw(t1, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000018:  0001a437  lui(s0, 0x1A000)  # s0=DISPATCH_CB_BASE (L1+0x1a000)
  0000001c:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000020:  6d028293  addi(t0, t0, 0x6D0)  # t0=COMPLETION_WR_PTR (L1+0x196d0)
  00000024:  0002a483  lw(s1, t0, 0)  # [COMPLETION_WR_PTR (L1+0x196d0)]
  00000028:  00000913  addi(s2, zero, 0)
  0000002c:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000030:  20428293  addi(t0, t0, 0x204)  # t0=NOC1+0x204
  00000034:  0002ab03  lw(s6, t0, 0)  # [NOC1+0x204]
  00000038:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  0000003c:  08028293  addi(t0, t0, 0x80)  # t0=DISPATCH_RELEASE_PENDING (L1+0x19080)
  00000040:  00000313  addi(t1, zero, 0)
  00000044:  0062a023  sw(t1, t0, 0)  # [DISPATCH_RELEASE_PENDING (L1+0x19080)]
  00000048:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  0000004c:  08428293  addi(t0, t0, 0x84)  # t0=DISPATCH_PAGE_CURSOR (L1+0x19084)
  00000050:  00000313  addi(t1, zero, 0)
  00000054:  0062a023  sw(t1, t0, 0)  # [DISPATCH_PAGE_CURSOR (L1+0x19084)]
  00000058:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  0000005c:  09028293  addi(t0, t0, 0x90)  # t0=DISPATCH_RELEASE_VALUE (L1+0x19090)
  00000060:  08000313  addi(t1, zero, 0x80)
  00000064:  0062a023  sw(t1, t0, 0)  # [DISPATCH_RELEASE_VALUE (L1+0x19090)]
dispatch_loop:
  00000068:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  0000006c:  c1d10337  lui(t1, 0xC1D10000)
  00000070:  00230313  addi(t1, t1, 2)
  00000074:  0062a023  sw(t1, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000078:  000082b7  lui(t0, 0x8000)  # t0=L1+0x8000
  0000007c:  6c028293  addi(t0, t0, 0x6C0)  # t0=CQ_SEM_BASE (L1.KERNEL_CONFIG+0x10)
dispatch_wait_page:
  00000080:  0ff0000f  fence()
  00000084:  0002a303  lw(t1, t0, 0)  # [CQ_SEM_BASE (L1.KERNEL_CONFIG+0x10)]
  00000088:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  0000008c:  01438393  addi(t2, t2, 0x14)  # t2=CQ_DEBUG+0x14 (L1+0x19014)
  00000090:  0063a023  sw(t1, t2, 0)  # [CQ_DEBUG+0x14 (L1+0x19014)]
  00000094:  00019e37  lui(t3, 0x19000)  # t3=CQ_DEBUG (L1+0x19000)
  00000098:  084e0e13  addi(t3, t3, 0x84)  # t3=DISPATCH_PAGE_CURSOR (L1+0x19084)
  0000009c:  000e2383  lw(t2, t3, 0)  # [DISPATCH_PAGE_CURSOR (L1+0x19084)]
  000000a0:  fe7300e3  beq(t1, t2, dispatch_wait_page)  # beq(t1, t2, -32)
  000000a4:  00138393  addi(t2, t2, 1)
  000000a8:  00019e37  lui(t3, 0x19000)  # t3=CQ_DEBUG (L1+0x19000)
  000000ac:  084e0e13  addi(t3, t3, 0x84)  # t3=DISPATCH_PAGE_CURSOR (L1+0x19084)
  000000b0:  007e2023  sw(t2, t3, 0)  # [DISPATCH_PAGE_CURSOR (L1+0x19084)]
  000000b4:  00019337  lui(t1, 0x19000)  # t1=CQ_DEBUG (L1+0x19000)
  000000b8:  01830313  addi(t1, t1, 0x18)  # t1=CQ_DEBUG+0x18 (L1+0x19018)
  000000bc:  00832023  sw(s0, t1, 0)  # [CQ_DEBUG+0x18 (L1+0x19018)], value=DISPATCH_CB_BASE (L1+0x1a000)
  000000c0:  00040c93  addi(s9, s0, 0)  # s9=DISPATCH_CB_BASE (L1+0x1a000)
  000000c4:  00044283  lbu(t0, s0, 0)  # [DISPATCH_CB_BASE (L1+0x1a000)]
  000000c8:  00019337  lui(t1, 0x19000)  # t1=CQ_DEBUG (L1+0x19000)
  000000cc:  00430313  addi(t1, t1, 4)  # t1=CQ_DEBUG+0x4 (L1+0x19004)
  000000d0:  00532023  sw(t0, t1, 0)  # [CQ_DEBUG+0x4 (L1+0x19004)]
  000000d4:  00600313  addi(t1, zero, 6)
  000000d8:  04628063  beq(t0, t1, cmd_packed_large)  # beq(t0, t1, 0x40)
  000000dc:  00500313  addi(t1, zero, 5)
  000000e0:  3e628063  beq(t0, t1, cmd_packed)  # beq(t0, t1, 0x3E0)
  000000e4:  00700313  addi(t1, zero, 7)
  000000e8:  4e628e63  beq(t0, t1, cmd_wait)  # beq(t0, t1, 0x4FC)
  000000ec:  01100313  addi(t1, zero, 0x11)
  000000f0:  60628063  beq(t0, t1, cmd_set_go)  # beq(t0, t1, 0x600)
  000000f4:  00e00313  addi(t1, zero, 0xE)
  000000f8:  64628063  beq(t0, t1, cmd_go)  # beq(t0, t1, 0x640)
  000000fc:  00300313  addi(t1, zero, 3)
  00000100:  74628863  beq(t0, t1, cmd_host)  # beq(t0, t1, 0x750)
  00000104:  01200313  addi(t1, zero, 0x12)
  00000108:  16628ee3  beq(t0, t1, cmd_timestamp)  # beq(t0, t1, 0x97C)
  0000010c:  00d00313  addi(t1, zero, 0xD)
  00000110:  3a6282e3  beq(t0, t1, dispatch_done)  # beq(t0, t1, 0xBA4)
  00000114:  2390006f  jal(zero, advance_page)  # jal(zero, 0xA38)
cmd_packed_large:
  00000118:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  0000011c:  c1d10337  lui(t1, 0xC1D10000)
  00000120:  60030313  addi(t1, t1, 0x600)
  00000124:  0062a023  sw(t1, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000128:  00245983  lhu(s3, s0, 2)  # [DISPATCH_CB_BASE+0x2 (L1+0x1a002)]
  0000012c:  00445a03  lhu(s4, s0, 4)  # [DISPATCH_CB_BASE+0x4 (L1+0x1a004)]
  00000130:  01040a93  addi(s5, s0, 0x10)  # s5=DISPATCH_CB_BASE+0x10 (L1+0x1a010)
  00000134:  000a8e13  addi(t3, s5, 0)  # t3=DISPATCH_CB_BASE+0x10 (L1+0x1a010)
  00000138:  00c00e93  addi(t4, zero, 0xC)
  0000013c:  03d98eb3  mul(t4, s3, t4)
  00000140:  01de0e33  add(t3, t3, t4)
  00000144:  00f00e93  addi(t4, zero, 0xF)
  00000148:  01de0e33  add(t3, t3, t4)
  0000014c:  ff000e93  addi(t4, zero, -16)
  00000150:  01de7e33  and(t3, t3, t4)
  00000154:  00100c13  addi(s8, zero, 1)
pl_loop:
  00000158:  36098063  beq(s3, zero, pl_done)  # beq(s3, zero, 0x360)
  0000015c:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000160:  c1d10337  lui(t1, 0xC1D10000)
  00000164:  60130313  addi(t1, t1, 0x601)
  00000168:  0062a023  sw(t1, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  0000016c:  000aae83  lw(t4, s5, 0)  # [DISPATCH_CB_BASE+0x10 (L1+0x1a010)]
  00000170:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000174:  00828293  addi(t0, t0, 8)  # t0=CQ_DEBUG+0x8 (L1+0x19008)
  00000178:  01d2a023  sw(t4, t0, 0)  # [CQ_DEBUG+0x8 (L1+0x19008)]
  0000017c:  004aaf03  lw(t5, s5, 4)  # [DISPATCH_CB_BASE+0x14 (L1+0x1a014)]
  00000180:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000184:  00c28293  addi(t0, t0, 0xC)  # t0=CQ_DEBUG+0xc (L1+0x1900c)
  00000188:  01e2a023  sw(t5, t0, 0)  # [CQ_DEBUG+0xc (L1+0x1900c)]
  0000018c:  008ad303  lhu(t1, s5, 8)  # [DISPATCH_CB_BASE+0x18 (L1+0x1a018)]
  00000190:  00130313  addi(t1, t1, 1)
  00000194:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000198:  01028293  addi(t0, t0, 0x10)  # t0=CQ_DEBUG+0x10 (L1+0x19010)
  0000019c:  0062a023  sw(t1, t0, 0)  # [CQ_DEBUG+0x10 (L1+0x19010)]
  000001a0:  00aacb83  lbu(s7, s5, 0xA)  # [DISPATCH_CB_BASE+0x1a (L1+0x1a01a)]
  000001a4:  00bacd83  lbu(s11, s5, 0xB)  # [DISPATCH_CB_BASE+0x1b (L1+0x1a01b)]
  000001a8:  001dfd93  andi(s11, s11, 1)
  000001ac:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000001b0:  c1d103b7  lui(t2, 0xC1D10000)
  000001b4:  60238393  addi(t2, t2, 0x602)
  000001b8:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  000001bc:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000001c0:  c1d103b7  lui(t2, 0xC1D10000)
  000001c4:  62038393  addi(t2, t2, 0x620)
  000001c8:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  000001cc:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000001d0:  02828293  addi(t0, t0, 0x28)  # t0=CQ_DEBUG+0x28 (L1+0x19028)
  000001d4:  01b2a023  sw(s11, t0, 0)  # [CQ_DEBUG+0x28 (L1+0x19028)]
  000001d8:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000001dc:  02c28293  addi(t0, t0, 0x2C)  # t0=CQ_DEBUG+0x2c (L1+0x1902c)
  000001e0:  0182a023  sw(s8, t0, 0)  # [CQ_DEBUG+0x2c (L1+0x1902c)]
  000001e4:  00030d13  addi(s10, t1, 0)
pl_burst_loop:
  000001e8:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000001ec:  c1d103b7  lui(t2, 0xC1D10000)
  000001f0:  62138393  addi(t2, t2, 0x621)
  000001f4:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  000001f8:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000001fc:  02028293  addi(t0, t0, 0x20)  # t0=CQ_DEBUG+0x20 (L1+0x19020)
  00000200:  01a2a023  sw(s10, t0, 0)  # [CQ_DEBUG+0x20 (L1+0x19020)]
  00000204:  200d0663  beq(s10, zero, pl_subcmd_done)  # beq(s10, zero, 0x20C)
  00000208:  00004fb7  lui(t6, 0x4000)  # t6=NOC_MAX_BURST_SIZE (L1+0x4000)
  0000020c:  0bafea63  bltu(t6, s10, pl_full_burst)  # bltu(t6, s10, 0xB4)
  00000210:  000d0313  addi(t1, s10, 0)
  00000214:  000c0c63  beq(s8, zero, pl_single_path_ready)  # beq(s8, zero, 0x18)
  00000218:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  0000021c:  20428293  addi(t0, t0, 0x204)  # t0=NOC1+0x204
.Lwr_ack_1:
  00000220:  0002a383  lw(t2, t0, 0)  # [NOC1+0x204]
  00000224:  ff63eee3  bltu(t2, s6, .Lwr_ack_1)  # bltu(t2, s6, -4)
  00000228:  0ff0000f  fence()
pl_single_path_ready:
  0000022c:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000230:  c1d103b7  lui(t2, 0xC1D10000)
  00000234:  62238393  addi(t2, t2, 0x622)
  00000238:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  0000023c:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000240:  04028293  addi(t0, t0, 0x40)  # t0=NOC1+0x40
.Lnoc_ready_2:
  00000244:  0002a383  lw(t2, t0, 0)  # [NOC1+0x40]
  00000248:  fe039ee3  bne(t2, zero, .Lnoc_ready_2)  # bne(t2, zero, -4)
  0000024c:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000250:  01c28293  addi(t0, t0, 0x1C)  # t0=NOC1+0x1c
  00000254:  0000a3b7  lui(t2, 0xA000)  # t2=NOC_CMD_STATIC_VC_5 (L1.KERNEL_CONFIG+0x1950)
  00000258:  1b238393  addi(t2, t2, 0x1B2)  # t2=NOC_CMD_WR_MCAST_UNLINK_FIELD (L1.KERNEL_CONFIG+0x1b02)
  0000025c:  0072a023  sw(t2, t0, 0)  # [NOC1+0x1c], value=NOC_CMD_WR_MCAST_UNLINK_FIELD (L1.KERNEL_CONFIG+0x1b02)
  00000260:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000264:  01c2a023  sw(t3, t0, 0)  # [NOC1]
  00000268:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  0000026c:  00c28293  addi(t0, t0, 0xC)  # t0=NOC1+0xc
  00000270:  01e2a023  sw(t5, t0, 0)  # [NOC1+0xc]
  00000274:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000278:  01028293  addi(t0, t0, 0x10)  # t0=NOC1+0x10
  0000027c:  00000393  addi(t2, zero, 0)
  00000280:  0072a023  sw(t2, t0, 0)  # [NOC1+0x10]
  00000284:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000288:  01428293  addi(t0, t0, 0x14)  # t0=NOC1+0x14
  0000028c:  01d2a023  sw(t4, t0, 0)  # [NOC1+0x14]
  00000290:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000294:  02028293  addi(t0, t0, 0x20)  # t0=NOC1+0x20
  00000298:  0062a023  sw(t1, t0, 0)  # [NOC1+0x20]
  0000029c:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  000002a0:  02428293  addi(t0, t0, 0x24)  # t0=NOC1+0x24
  000002a4:  00000393  addi(t2, zero, 0)
  000002a8:  0072a023  sw(t2, t0, 0)  # [NOC1+0x24]
  000002ac:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  000002b0:  04028293  addi(t0, t0, 0x40)  # t0=NOC1+0x40
  000002b4:  00100393  addi(t2, zero, 1)
  000002b8:  0072a023  sw(t2, t0, 0)  # [NOC1+0x40]
  000002bc:  0b00006f  jal(zero, pl_burst_sent)  # jal(zero, 0xB0)
pl_full_burst:
  000002c0:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000002c4:  c1d103b7  lui(t2, 0xC1D10000)
  000002c8:  62438393  addi(t2, t2, 0x624)
  000002cc:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  000002d0:  000c0c63  beq(s8, zero, pl_full_path_ready)  # beq(s8, zero, 0x18)
  000002d4:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  000002d8:  20428293  addi(t0, t0, 0x204)  # t0=NOC1+0x204
.Lwr_ack_3:
  000002dc:  0002a383  lw(t2, t0, 0)  # [NOC1+0x204]
  000002e0:  ff63eee3  bltu(t2, s6, .Lwr_ack_3)  # bltu(t2, s6, -4)
  000002e4:  0ff0000f  fence()
pl_full_path_ready:
  000002e8:  000f8313  addi(t1, t6, 0)  # t1=NOC_MAX_BURST_SIZE (L1+0x4000)
  000002ec:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  000002f0:  04028293  addi(t0, t0, 0x40)  # t0=NOC1+0x40
.Lnoc_ready_4:
  000002f4:  0002a383  lw(t2, t0, 0)  # [NOC1+0x40]
  000002f8:  fe039ee3  bne(t2, zero, .Lnoc_ready_4)  # bne(t2, zero, -4)
  000002fc:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000300:  01c28293  addi(t0, t0, 0x1C)  # t0=NOC1+0x1c
  00000304:  0000a3b7  lui(t2, 0xA000)  # t2=NOC_CMD_STATIC_VC_5 (L1.KERNEL_CONFIG+0x1950)
  00000308:  1b238393  addi(t2, t2, 0x1B2)  # t2=NOC_CMD_WR_MCAST_UNLINK_FIELD (L1.KERNEL_CONFIG+0x1b02)
  0000030c:  0072a023  sw(t2, t0, 0)  # [NOC1+0x1c], value=NOC_CMD_WR_MCAST_UNLINK_FIELD (L1.KERNEL_CONFIG+0x1b02)
  00000310:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000314:  01c2a023  sw(t3, t0, 0)  # [NOC1]
  00000318:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  0000031c:  00c28293  addi(t0, t0, 0xC)  # t0=NOC1+0xc
  00000320:  01e2a023  sw(t5, t0, 0)  # [NOC1+0xc]
  00000324:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000328:  01028293  addi(t0, t0, 0x10)  # t0=NOC1+0x10
  0000032c:  00000393  addi(t2, zero, 0)
  00000330:  0072a023  sw(t2, t0, 0)  # [NOC1+0x10]
  00000334:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000338:  01428293  addi(t0, t0, 0x14)  # t0=NOC1+0x14
  0000033c:  01d2a023  sw(t4, t0, 0)  # [NOC1+0x14]
  00000340:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000344:  02028293  addi(t0, t0, 0x20)  # t0=NOC1+0x20
  00000348:  0062a023  sw(t1, t0, 0)  # [NOC1+0x20], value=NOC_MAX_BURST_SIZE (L1+0x4000)
  0000034c:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000350:  02428293  addi(t0, t0, 0x24)  # t0=NOC1+0x24
  00000354:  00000393  addi(t2, zero, 0)
  00000358:  0072a023  sw(t2, t0, 0)  # [NOC1+0x24]
  0000035c:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000360:  04028293  addi(t0, t0, 0x40)  # t0=NOC1+0x40
  00000364:  00100393  addi(t2, zero, 1)
  00000368:  0072a023  sw(t2, t0, 0)  # [NOC1+0x40]
pl_burst_sent:
  0000036c:  00100c13  addi(s8, zero, 1)
  00000370:  017b0b33  add(s6, s6, s7)
  00000374:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000378:  02428293  addi(t0, t0, 0x24)  # t0=CQ_DEBUG+0x24 (L1+0x19024)
  0000037c:  0062a023  sw(t1, t0, 0)  # [CQ_DEBUG+0x24 (L1+0x19024)], value=NOC_MAX_BURST_SIZE (L1+0x4000)
  00000380:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000384:  03028293  addi(t0, t0, 0x30)  # t0=CQ_DEBUG+0x30 (L1+0x19030)
  00000388:  0162a023  sw(s6, t0, 0)  # [CQ_DEBUG+0x30 (L1+0x19030)]
  0000038c:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000390:  c1d103b7  lui(t2, 0xC1D10000)
  00000394:  60338393  addi(t2, t2, 0x603)
  00000398:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  0000039c:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  000003a0:  04028293  addi(t0, t0, 0x40)  # t0=NOC1+0x40
.Lnoc_ready_5:
  000003a4:  0002a383  lw(t2, t0, 0)  # [NOC1+0x40]
  000003a8:  fe039ee3  bne(t2, zero, .Lnoc_ready_5)  # bne(t2, zero, -4)
  000003ac:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000003b0:  c1d103b7  lui(t2, 0xC1D10000)
  000003b4:  60438393  addi(t2, t2, 0x604)
  000003b8:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  000003bc:  006e0e33  add(t3, t3, t1)
  000003c0:  006f0f33  add(t5, t5, t1)
  000003c4:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000003c8:  c1d103b7  lui(t2, 0xC1D10000)
  000003cc:  62538393  addi(t2, t2, 0x625)
  000003d0:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  000003d4:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000003d8:  03428293  addi(t0, t0, 0x34)  # t0=CQ_DEBUG+0x34 (L1+0x19034)
  000003dc:  01c2a023  sw(t3, t0, 0)  # [CQ_DEBUG+0x34 (L1+0x19034)]
  000003e0:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000003e4:  03828293  addi(t0, t0, 0x38)  # t0=CQ_DEBUG+0x38 (L1+0x19038)
  000003e8:  01e2a023  sw(t5, t0, 0)  # [CQ_DEBUG+0x38 (L1+0x19038)]
  000003ec:  406d0d33  sub(s10, s10, t1)
  000003f0:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000003f4:  c1d103b7  lui(t2, 0xC1D10000)
  000003f8:  62638393  addi(t2, t2, 0x626)
  000003fc:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000400:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000404:  02028293  addi(t0, t0, 0x20)  # t0=CQ_DEBUG+0x20 (L1+0x19020)
  00000408:  01a2a023  sw(s10, t0, 0)  # [CQ_DEBUG+0x20 (L1+0x19020)]
  0000040c:  dddff06f  jal(zero, pl_burst_loop)  # jal(zero, -548)
pl_subcmd_done:
  00000410:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000414:  c1d103b7  lui(t2, 0xC1D10000)
  00000418:  62738393  addi(t2, t2, 0x627)
  0000041c:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000420:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000424:  02828293  addi(t0, t0, 0x28)  # t0=CQ_DEBUG+0x28 (L1+0x19028)
  00000428:  01b2a023  sw(s11, t0, 0)  # [CQ_DEBUG+0x28 (L1+0x19028)]
  0000042c:  020d8463  beq(s11, zero, pl_keep_linked)  # beq(s11, zero, 0x28)
  00000430:  00100c13  addi(s8, zero, 1)
  00000434:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000438:  c1d103b7  lui(t2, 0xC1D10000)
  0000043c:  62838393  addi(t2, t2, 0x628)
  00000440:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000444:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000448:  02c28293  addi(t0, t0, 0x2C)  # t0=CQ_DEBUG+0x2c (L1+0x1902c)
  0000044c:  0182a023  sw(s8, t0, 0)  # [CQ_DEBUG+0x2c (L1+0x1902c)]
  00000450:  0240006f  jal(zero, pl_round_subcmd)  # jal(zero, 0x24)
pl_keep_linked:
  00000454:  00000c13  addi(s8, zero, 0)
  00000458:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  0000045c:  c1d103b7  lui(t2, 0xC1D10000)
  00000460:  62938393  addi(t2, t2, 0x629)
  00000464:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000468:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  0000046c:  02c28293  addi(t0, t0, 0x2C)  # t0=CQ_DEBUG+0x2c (L1+0x1902c)
  00000470:  0182a023  sw(s8, t0, 0)  # [CQ_DEBUG+0x2c (L1+0x1902c)]
pl_round_subcmd:
  00000474:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000478:  c1d103b7  lui(t2, 0xC1D10000)
  0000047c:  62a38393  addi(t2, t2, 0x62A)
  00000480:  0072a023  sw(t2, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000484:  00f00e93  addi(t4, zero, 0xF)
  00000488:  01de0e33  add(t3, t3, t4)
  0000048c:  ff000e93  addi(t4, zero, -16)
  00000490:  01de7e33  and(t3, t3, t4)
  00000494:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000498:  03428293  addi(t0, t0, 0x34)  # t0=CQ_DEBUG+0x34 (L1+0x19034)
  0000049c:  01c2a023  sw(t3, t0, 0)  # [CQ_DEBUG+0x34 (L1+0x19034)]
  000004a0:  00ca8a93  addi(s5, s5, 0xC)  # s5=DISPATCH_CB_BASE+0x1c (L1+0x1a01c)
  000004a4:  fff98993  addi(s3, s3, -1)
  000004a8:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  000004ac:  03c28293  addi(t0, t0, 0x3C)  # t0=CQ_DEBUG+0x3c (L1+0x1903c)
  000004b0:  0132a023  sw(s3, t0, 0)  # [CQ_DEBUG+0x3c (L1+0x1903c)]
  000004b4:  ca5ff06f  jal(zero, pl_loop)  # jal(zero, -860)
pl_done:
  000004b8:  000e0413  addi(s0, t3, 0)
  000004bc:  69c0006f  jal(zero, release_and_continue)  # jal(zero, 0x69C)
cmd_packed:
  000004c0:  00144c03  lbu(s8, s0, 1)
  000004c4:  00245303  lhu(t1, s0, 2)
  000004c8:  00645383  lhu(t2, s0, 6)
  000004cc:  00842e03  lw(t3, s0, 8)
  000004d0:  01040e93  addi(t4, s0, 0x10)
  000004d4:  000e8f13  addi(t5, t4, 0)
  000004d8:  00231293  slli(t0, t1, 2)
  000004dc:  005f0f33  add(t5, t5, t0)
  000004e0:  00f00293  addi(t0, zero, 0xF)
  000004e4:  005f0f33  add(t5, t5, t0)
  000004e8:  ff000293  addi(t0, zero, -16)
  000004ec:  005f7f33  and(t5, t5, t0)
  000004f0:  000f0d13  addi(s10, t5, 0)
  000004f4:  00038d93  addi(s11, t2, 0)
  000004f8:  00f00293  addi(t0, zero, 0xF)
  000004fc:  005d8db3  add(s11, s11, t0)
  00000500:  ff000293  addi(t0, zero, -16)
  00000504:  005dfdb3  and(s11, s11, t0)
pw_loop:
  00000508:  0c030263  beq(t1, zero, pw_done)  # beq(t1, zero, 0xC4)
  0000050c:  000ea283  lw(t0, t4, 0)
  00000510:  ffb309b7  lui(s3, 0xFFB30000)  # s3=NOC1
  00000514:  04098993  addi(s3, s3, 0x40)  # s3=NOC1+0x40
.Lnoc_ready_6:
  00000518:  0009aa03  lw(s4, s3, 0)  # [NOC1+0x40]
  0000051c:  fe0a1ee3  bne(s4, zero, .Lnoc_ready_6)  # bne(s4, zero, -4)
  00000520:  ffb309b7  lui(s3, 0xFFB30000)  # s3=NOC1
  00000524:  01c98993  addi(s3, s3, 0x1C)  # s3=NOC1+0x1c
  00000528:  00002a37  lui(s4, 0x2000)  # s4=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  0000052c:  092a0a13  addi(s4, s4, 0x92)  # s4=NOC_CMD_WR_FIELD (L1+0x2092)
  00000530:  0149a023  sw(s4, s3, 0)  # [NOC1+0x1c], value=NOC_CMD_WR_FIELD (L1+0x2092)
  00000534:  ffb309b7  lui(s3, 0xFFB30000)  # s3=NOC1
  00000538:  01e9a023  sw(t5, s3, 0)  # [NOC1]
  0000053c:  ffb309b7  lui(s3, 0xFFB30000)  # s3=NOC1
  00000540:  00c98993  addi(s3, s3, 0xC)  # s3=NOC1+0xc
  00000544:  01c9a023  sw(t3, s3, 0)  # [NOC1+0xc]
  00000548:  ffb309b7  lui(s3, 0xFFB30000)  # s3=NOC1
  0000054c:  01098993  addi(s3, s3, 0x10)  # s3=NOC1+0x10
  00000550:  00000a13  addi(s4, zero, 0)
  00000554:  0149a023  sw(s4, s3, 0)  # [NOC1+0x10]
  00000558:  ffb309b7  lui(s3, 0xFFB30000)  # s3=NOC1
  0000055c:  01498993  addi(s3, s3, 0x14)  # s3=NOC1+0x14
  00000560:  0059a023  sw(t0, s3, 0)  # [NOC1+0x14]
  00000564:  ffb309b7  lui(s3, 0xFFB30000)  # s3=NOC1
  00000568:  02098993  addi(s3, s3, 0x20)  # s3=NOC1+0x20
  0000056c:  0079a023  sw(t2, s3, 0)  # [NOC1+0x20]
  00000570:  ffb309b7  lui(s3, 0xFFB30000)  # s3=NOC1
  00000574:  02498993  addi(s3, s3, 0x24)  # s3=NOC1+0x24
  00000578:  00000a13  addi(s4, zero, 0)
  0000057c:  0149a023  sw(s4, s3, 0)  # [NOC1+0x24]
  00000580:  ffb309b7  lui(s3, 0xFFB30000)  # s3=NOC1
  00000584:  04098993  addi(s3, s3, 0x40)  # s3=NOC1+0x40
  00000588:  00100a13  addi(s4, zero, 1)
  0000058c:  0149a023  sw(s4, s3, 0)  # [NOC1+0x40]
  00000590:  001b0b13  addi(s6, s6, 1)
  00000594:  ffb309b7  lui(s3, 0xFFB30000)  # s3=NOC1
  00000598:  04098993  addi(s3, s3, 0x40)  # s3=NOC1+0x40
.Lnoc_ready_7:
  0000059c:  0009aa03  lw(s4, s3, 0)  # [NOC1+0x40]
  000005a0:  fe0a1ee3  bne(s4, zero, .Lnoc_ready_7)  # bne(s4, zero, -4)
  000005a4:  002c7293  andi(t0, s8, 2)
  000005a8:  00029c63  bne(t0, zero, pw_no_stride)  # bne(t0, zero, 0x18)
  000005ac:  007f0f33  add(t5, t5, t2)
  000005b0:  00f00293  addi(t0, zero, 0xF)
  000005b4:  005f0f33  add(t5, t5, t0)
  000005b8:  ff000293  addi(t0, zero, -16)
  000005bc:  005f7f33  and(t5, t5, t0)
pw_no_stride:
  000005c0:  004e8e93  addi(t4, t4, 4)
  000005c4:  fff30313  addi(t1, t1, -1)
  000005c8:  f41ff06f  jal(zero, pw_loop)  # jal(zero, -192)
pw_done:
  000005cc:  002c7293  andi(t0, s8, 2)
  000005d0:  00028663  beq(t0, zero, pw_done_ptr_ready)  # beq(t0, zero, 0xC)
  000005d4:  000d0f13  addi(t5, s10, 0)
  000005d8:  01bf0f33  add(t5, t5, s11)
pw_done_ptr_ready:
  000005dc:  000f0413  addi(s0, t5, 0)
  000005e0:  5780006f  jal(zero, release_and_continue)  # jal(zero, 0x578)
cmd_wait:
  000005e4:  00144283  lbu(t0, s0, 1)
  000005e8:  0012f313  andi(t1, t0, 1)
  000005ec:  00030c63  beq(t1, zero, wait_no_barrier)  # beq(t1, zero, 0x18)
  000005f0:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  000005f4:  20438393  addi(t2, t2, 0x204)  # t2=NOC1+0x204
.Lwr_ack_8:
  000005f8:  0003ae03  lw(t3, t2, 0)  # [NOC1+0x204]
  000005fc:  ff6e6ee3  bltu(t3, s6, .Lwr_ack_8)  # bltu(t3, s6, -4)
  00000600:  0ff0000f  fence()
wait_no_barrier:
  00000604:  0082f313  andi(t1, t0, 8)
  00000608:  06030e63  beq(t1, zero, wait_clear)  # beq(t1, zero, 0x7C)
  0000060c:  00245383  lhu(t2, s0, 2)
  00000610:  00842e03  lw(t3, s0, 8)
  00000614:  00019eb7  lui(t4, 0x19000)  # t4=CQ_DEBUG (L1+0x19000)
  00000618:  c1d10f37  lui(t5, 0xC1D10000)
  0000061c:  700f0f13  addi(t5, t5, 0x700)
  00000620:  01eea023  sw(t5, t4, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000624:  00019eb7  lui(t4, 0x19000)  # t4=CQ_DEBUG (L1+0x19000)
  00000628:  028e8e93  addi(t4, t4, 0x28)  # t4=CQ_DEBUG+0x28 (L1+0x19028)
  0000062c:  007ea023  sw(t2, t4, 0)  # [CQ_DEBUG+0x28 (L1+0x19028)]
  00000630:  00019eb7  lui(t4, 0x19000)  # t4=CQ_DEBUG (L1+0x19000)
  00000634:  02ce8e93  addi(t4, t4, 0x2C)  # t4=CQ_DEBUG+0x2c (L1+0x1902c)
  00000638:  01cea023  sw(t3, t4, 0)  # [CQ_DEBUG+0x2c (L1+0x1902c)]
  0000063c:  00c39393  slli(t2, t2, 0xC)
  00000640:  ffb40eb7  lui(t4, 0xFFB40000)  # t4=STREAM_BASE (STREAM_REGS)
  00000644:  4a4e8e93  addi(t4, t4, 0x4A4)  # t4=STREAM_REGS+0x4a4
  00000648:  01d383b3  add(t2, t2, t4)
wait_stream_loop:
  0000064c:  0003ae83  lw(t4, t2, 0)
  00000650:  00019f37  lui(t5, 0x19000)  # t5=CQ_DEBUG (L1+0x19000)
  00000654:  030f0f13  addi(t5, t5, 0x30)  # t5=CQ_DEBUG+0x30 (L1+0x19030)
  00000658:  01df2023  sw(t4, t5, 0)  # [CQ_DEBUG+0x30 (L1+0x19030)]
  0000065c:  00020f37  lui(t5, 0x20000)  # t5=L1+0x20000
  00000660:  ffff0f13  addi(t5, t5, -1)  # t5=L1+0x1ffff
  00000664:  01eefeb3  and(t4, t4, t5)
  00000668:  41ce8eb3  sub(t4, t4, t3)
  0000066c:  00fe9e93  slli(t4, t4, 0xF)
  00000670:  fc0ecee3  blt(t4, zero, wait_stream_loop)  # blt(t4, zero, -36)
wait_stream_done:
  00000674:  00019eb7  lui(t4, 0x19000)  # t4=CQ_DEBUG (L1+0x19000)
  00000678:  c1d10f37  lui(t5, 0xC1D10000)
  0000067c:  701f0f13  addi(t5, t5, 0x701)
  00000680:  01eea023  sw(t5, t4, 0)  # [CQ_DEBUG (L1+0x19000)]
wait_clear:
  00000684:  0102f313  andi(t1, t0, 0x10)
  00000688:  06030063  beq(t1, zero, wait_done)  # beq(t1, zero, 0x60)
  0000068c:  00245383  lhu(t2, s0, 2)
  00000690:  00c39393  slli(t2, t2, 0xC)
  00000694:  ffb40eb7  lui(t4, 0xFFB40000)  # t4=STREAM_BASE (STREAM_REGS)
  00000698:  4a4e8e93  addi(t4, t4, 0x4A4)  # t4=STREAM_REGS+0x4a4
  0000069c:  01d38f33  add(t5, t2, t4)
  000006a0:  000f2e03  lw(t3, t5, 0)
  000006a4:  00020eb7  lui(t4, 0x20000)  # t4=L1+0x20000
  000006a8:  fffe8e93  addi(t4, t4, -1)  # t4=L1+0x1ffff
  000006ac:  01de7e33  and(t3, t3, t4)
  000006b0:  41c00e33  sub(t3, zero, t3)
  000006b4:  006e1e13  slli(t3, t3, 6)
  000006b8:  ffb40eb7  lui(t4, 0xFFB40000)  # t4=STREAM_BASE (STREAM_REGS)
  000006bc:  438e8e93  addi(t4, t4, 0x438)  # t4=STREAM_REGS+0x438
  000006c0:  01d38f33  add(t5, t2, t4)
  000006c4:  01cf2023  sw(t3, t5, 0)
  000006c8:  ffb40eb7  lui(t4, 0xFFB40000)  # t4=STREAM_BASE (STREAM_REGS)
  000006cc:  4a4e8e93  addi(t4, t4, 0x4A4)  # t4=STREAM_REGS+0x4a4
  000006d0:  01d38f33  add(t5, t2, t4)
wait_clear_drain:
  000006d4:  000f2e03  lw(t3, t5, 0)
  000006d8:  00020eb7  lui(t4, 0x20000)  # t4=L1+0x20000
  000006dc:  fffe8e93  addi(t4, t4, -1)  # t4=L1+0x1ffff
  000006e0:  01de7e33  and(t3, t3, t4)
  000006e4:  fe0e18e3  bne(t3, zero, wait_clear_drain)  # bne(t3, zero, -16)
wait_done:
  000006e8:  01040413  addi(s0, s0, 0x10)
  000006ec:  46c0006f  jal(zero, release_and_continue)  # jal(zero, 0x46C)
cmd_set_go:
  000006f0:  00442283  lw(t0, s0, 4)
  000006f4:  01040313  addi(t1, s0, 0x10)
  000006f8:  000b03b7  lui(t2, 0xB0000)  # t2=GO_SIGNAL_NOC_DATA (L1.DATA_BUFFER_SPACE+0x79000)
  000006fc:  00229293  slli(t0, t0, 2)
.Lcopy_9:
  00000700:  00028e63  beq(t0, zero, .Lcopy_done_10)  # beq(t0, zero, 0x1C)
  00000704:  00032e03  lw(t3, t1, 0)
  00000708:  01c3a023  sw(t3, t2, 0)  # [GO_SIGNAL_NOC_DATA (L1.DATA_BUFFER_SPACE+0x79000)]
  0000070c:  00430313  addi(t1, t1, 4)
  00000710:  00438393  addi(t2, t2, 4)  # t2=GO_SIGNAL_NOC_DATA+0x4 (L1.DATA_BUFFER_SPACE+0x79004)
  00000714:  ffc28293  addi(t0, t0, -4)
  00000718:  fe9ff06f  jal(zero, .Lcopy_9)  # jal(zero, -24)
.Lcopy_done_10:
  0000071c:  00030413  addi(s0, t1, 0)
  00000720:  00540433  add(s0, s0, t0)
  00000724:  00f00293  addi(t0, zero, 0xF)
  00000728:  00540433  add(s0, s0, t0)
  0000072c:  ff000293  addi(t0, zero, -16)
  00000730:  00547433  and(s0, s0, t0)
  00000734:  4240006f  jal(zero, release_and_continue)  # jal(zero, 0x424)
cmd_go:
  00000738:  00144283  lbu(t0, s0, 1)
  0000073c:  00244e03  lbu(t3, s0, 2)
  00000740:  008e1e13  slli(t3, t3, 8)
  00000744:  01c2e2b3  or(t0, t0, t3)
  00000748:  00344e03  lbu(t3, s0, 3)
  0000074c:  010e1e13  slli(t3, t3, 0x10)
  00000750:  01c2e2b3  or(t0, t0, t3)
  00000754:  00444e03  lbu(t3, s0, 4)
  00000758:  018e1e13  slli(t3, t3, 0x18)
  0000075c:  01c2e2b3  or(t0, t0, t3)
  00000760:  00644303  lbu(t1, s0, 6)
  00000764:  00744383  lbu(t2, s0, 7)
  00000768:  00019e37  lui(t3, 0x19000)  # t3=CQ_DEBUG (L1+0x19000)
  0000076c:  020e0e13  addi(t3, t3, 0x20)  # t3=CQ_DEBUG+0x20 (L1+0x19020)
  00000770:  005e2023  sw(t0, t3, 0)  # [CQ_DEBUG+0x20 (L1+0x19020)]
  00000774:  00019e37  lui(t3, 0x19000)  # t3=CQ_DEBUG (L1+0x19000)
  00000778:  024e0e13  addi(t3, t3, 0x24)  # t3=CQ_DEBUG+0x24 (L1+0x19024)
  0000077c:  006e2023  sw(t1, t3, 0)  # [CQ_DEBUG+0x24 (L1+0x19024)]
  00000780:  000b0e37  lui(t3, 0xB0000)  # t3=GO_SIGNAL_NOC_DATA (L1.DATA_BUFFER_SPACE+0x79000)
  00000784:  00239393  slli(t2, t2, 2)
  00000788:  007e0e33  add(t3, t3, t2)
  0000078c:  00019fb7  lui(t6, 0x19000)  # t6=CQ_DEBUG (L1+0x19000)
  00000790:  100f8f93  addi(t6, t6, 0x100)  # t6=GO_SIGNAL_VALUE (L1+0x19100)
  00000794:  005fa023  sw(t0, t6, 0)  # [GO_SIGNAL_VALUE (L1+0x19100)]
go_loop:
  00000798:  0a030863  beq(t1, zero, go_done)  # beq(t1, zero, 0xB0)
  0000079c:  000e2383  lw(t2, t3, 0)
  000007a0:  37000e93  addi(t4, zero, 0x370)
  000007a4:  00400993  addi(s3, zero, 4)
  000007a8:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  000007ac:  840f0f13  addi(t5, t5, -1984)  # t5=NOC1+0x840
.Lnoc_ready_11:
  000007b0:  000f2a03  lw(s4, t5, 0)  # [NOC1+0x840]
  000007b4:  fe0a1ee3  bne(s4, zero, .Lnoc_ready_11)  # bne(s4, zero, -4)
  000007b8:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  000007bc:  81cf0f13  addi(t5, t5, -2020)  # t5=NOC1+0x81c
  000007c0:  00002a37  lui(s4, 0x2000)  # s4=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  000007c4:  092a0a13  addi(s4, s4, 0x92)  # s4=NOC_CMD_WR_FIELD (L1+0x2092)
  000007c8:  014f2023  sw(s4, t5, 0)  # [NOC1+0x81c], value=NOC_CMD_WR_FIELD (L1+0x2092)
  000007cc:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  000007d0:  800f0f13  addi(t5, t5, -2048)  # t5=NOC1+0x800
  000007d4:  01ff2023  sw(t6, t5, 0)  # [NOC1+0x800], value=GO_SIGNAL_VALUE (L1+0x19100)
  000007d8:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  000007dc:  80cf0f13  addi(t5, t5, -2036)  # t5=NOC1+0x80c
  000007e0:  01df2023  sw(t4, t5, 0)  # [NOC1+0x80c]
  000007e4:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  000007e8:  810f0f13  addi(t5, t5, -2032)  # t5=NOC1+0x810
  000007ec:  00000a13  addi(s4, zero, 0)
  000007f0:  014f2023  sw(s4, t5, 0)  # [NOC1+0x810]
  000007f4:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  000007f8:  814f0f13  addi(t5, t5, -2028)  # t5=NOC1+0x814
  000007fc:  007f2023  sw(t2, t5, 0)  # [NOC1+0x814]
  00000800:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000804:  820f0f13  addi(t5, t5, -2016)  # t5=NOC1+0x820
  00000808:  013f2023  sw(s3, t5, 0)  # [NOC1+0x820]
  0000080c:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000810:  824f0f13  addi(t5, t5, -2012)  # t5=NOC1+0x824
  00000814:  00000a13  addi(s4, zero, 0)
  00000818:  014f2023  sw(s4, t5, 0)  # [NOC1+0x824]
  0000081c:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000820:  840f0f13  addi(t5, t5, -1984)  # t5=NOC1+0x840
  00000824:  00100a13  addi(s4, zero, 1)
  00000828:  014f2023  sw(s4, t5, 0)  # [NOC1+0x840]
  0000082c:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000830:  840f0f13  addi(t5, t5, -1984)  # t5=NOC1+0x840
.Lnoc_ready_12:
  00000834:  000f2983  lw(s3, t5, 0)  # [NOC1+0x840]
  00000838:  fe099ee3  bne(s3, zero, .Lnoc_ready_12)  # bne(s3, zero, -4)
  0000083c:  004e0e13  addi(t3, t3, 4)
  00000840:  fff30313  addi(t1, t1, -1)
  00000844:  f55ff06f  jal(zero, go_loop)  # jal(zero, -172)
go_done:
  00000848:  01040413  addi(s0, s0, 0x10)
  0000084c:  30c0006f  jal(zero, release_and_continue)  # jal(zero, 0x30C)
cmd_host:
  00000850:  00019337  lui(t1, 0x19000)  # t1=CQ_DEBUG (L1+0x19000)
  00000854:  c1d103b7  lui(t2, 0xC1D10000)
  00000858:  30038393  addi(t2, t2, 0x300)
  0000085c:  00732023  sw(t2, t1, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000860:  00842283  lw(t0, s0, 8)
  00000864:  00019337  lui(t1, 0x19000)  # t1=CQ_DEBUG (L1+0x19000)
  00000868:  00830313  addi(t1, t1, 8)  # t1=CQ_DEBUG+0x8 (L1+0x19008)
  0000086c:  00532023  sw(t0, t1, 0)  # [CQ_DEBUG+0x8 (L1+0x19008)]
  00000870:  00449313  slli(t1, s1, 4)
  00000874:  00019eb7  lui(t4, 0x19000)  # t4=CQ_DEBUG (L1+0x19000)
  00000878:  00ce8e93  addi(t4, t4, 0xC)  # t4=CQ_DEBUG+0xc (L1+0x1900c)
  0000087c:  006ea023  sw(t1, t4, 0)  # [CQ_DEBUG+0xc (L1+0x1900c)]
  00000880:  00019eb7  lui(t4, 0x19000)  # t4=CQ_DEBUG (L1+0x19000)
  00000884:  c1d10f37  lui(t5, 0xC1D10000)
  00000888:  301f0f13  addi(t5, t5, 0x301)
  0000088c:  01eea023  sw(t5, t4, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000890:  ffb20eb7  lui(t4, 0xFFB20000)  # t4=NOC_TARG_ADDR_LO (NOC0)
  00000894:  204e8e93  addi(t4, t4, 0x204)  # t4=NOC_STATUS_BASE+0x4 (NOC0+0x204)
  00000898:  000eab03  lw(s6, t4, 0)  # [NOC_STATUS_BASE+0x4 (NOC0+0x204)]
  0000089c:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  000008a0:  04038393  addi(t2, t2, 0x40)  # t2=NOC1+0x40
.Lnoc_ready_13:
  000008a4:  0003ae03  lw(t3, t2, 0)  # [NOC1+0x40]
  000008a8:  fe0e1ee3  bne(t3, zero, .Lnoc_ready_13)  # bne(t3, zero, -4)
  000008ac:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  000008b0:  01c38393  addi(t2, t2, 0x1C)  # t2=NOC1+0x1c
  000008b4:  00002e37  lui(t3, 0x2000)  # t3=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  000008b8:  092e0e13  addi(t3, t3, 0x92)  # t3=NOC_CMD_WR_FIELD (L1+0x2092)
  000008bc:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x1c], value=NOC_CMD_WR_FIELD (L1+0x2092)
  000008c0:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  000008c4:  0083a023  sw(s0, t2, 0)  # [NOC1]
  000008c8:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  000008cc:  00c38393  addi(t2, t2, 0xC)  # t2=NOC1+0xc
  000008d0:  0063a023  sw(t1, t2, 0)  # [NOC1+0xc]
  000008d4:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  000008d8:  01038393  addi(t2, t2, 0x10)  # t2=NOC1+0x10
  000008dc:  10000e37  lui(t3, 0x10000000)  # t3=NOC_PCIE_MID
  000008e0:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x10], value=NOC_PCIE_MID
  000008e4:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  000008e8:  01438393  addi(t2, t2, 0x14)  # t2=NOC1+0x14
  000008ec:  01000e37  lui(t3, 0x1000000)
  000008f0:  613e0e13  addi(t3, t3, 0x613)  # t3=PCIE_NOC_XY
  000008f4:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x14], value=PCIE_NOC_XY
  000008f8:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  000008fc:  02038393  addi(t2, t2, 0x20)  # t2=NOC1+0x20
  00000900:  0053a023  sw(t0, t2, 0)  # [NOC1+0x20]
  00000904:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  00000908:  02438393  addi(t2, t2, 0x24)  # t2=NOC1+0x24
  0000090c:  00000e13  addi(t3, zero, 0)
  00000910:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x24]
  00000914:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  00000918:  04038393  addi(t2, t2, 0x40)  # t2=NOC1+0x40
  0000091c:  00100e13  addi(t3, zero, 1)
  00000920:  01c3a023  sw(t3, t2, 0)  # [NOC1+0x40]
  00000924:  001b0b13  addi(s6, s6, 1)
  00000928:  00019eb7  lui(t4, 0x19000)  # t4=CQ_DEBUG (L1+0x19000)
  0000092c:  c1d10f37  lui(t5, 0xC1D10000)
  00000930:  302f0f13  addi(t5, t5, 0x302)
  00000934:  01eea023  sw(t5, t4, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000938:  ffb303b7  lui(t2, 0xFFB30000)  # t2=NOC1
  0000093c:  20438393  addi(t2, t2, 0x204)  # t2=NOC1+0x204
.Lwr_ack_14:
  00000940:  0003ae03  lw(t3, t2, 0)  # [NOC1+0x204]
  00000944:  ff6e6ee3  bltu(t3, s6, .Lwr_ack_14)  # bltu(t3, s6, -4)
  00000948:  00019eb7  lui(t4, 0x19000)  # t4=CQ_DEBUG (L1+0x19000)
  0000094c:  c1d10f37  lui(t5, 0xC1D10000)
  00000950:  303f0f13  addi(t5, t5, 0x303)
  00000954:  01eea023  sw(t5, t4, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000958:  10048493  addi(s1, s1, 0x100)
  0000095c:  046003b7  lui(t2, 0x4600000)
  00000960:  01038393  addi(t2, t2, 0x10)
  00000964:  0074e863  bltu(s1, t2, host_no_wrap)  # bltu(s1, t2, 0x10)
  00000968:  044004b7  lui(s1, 0x4400000)
  0000096c:  01048493  addi(s1, s1, 0x10)
  00000970:  00194913  xori(s2, s2, 1)
host_no_wrap:
  00000974:  00048293  addi(t0, s1, 0)
  00000978:  01f91313  slli(t1, s2, 0x1F)
  0000097c:  0062e2b3  or(t0, t0, t1)
  00000980:  00019337  lui(t1, 0x19000)  # t1=CQ_DEBUG (L1+0x19000)
  00000984:  6d030313  addi(t1, t1, 0x6D0)  # t1=COMPLETION_WR_PTR (L1+0x196d0)
  00000988:  00532023  sw(t0, t1, 0)  # [COMPLETION_WR_PTR (L1+0x196d0)]
  0000098c:  00019337  lui(t1, 0x19000)  # t1=CQ_DEBUG (L1+0x19000)
  00000990:  6d030313  addi(t1, t1, 0x6D0)  # t1=COMPLETION_WR_PTR (L1+0x196d0)
  00000994:  400003b7  lui(t2, 0x40000000)
  00000998:  08038393  addi(t2, t2, 0x80)  # t2=HOST_COMPLETION_WR_PTR_OFF
  0000099c:  00400e13  addi(t3, zero, 4)
  000009a0:  00019eb7  lui(t4, 0x19000)  # t4=CQ_DEBUG (L1+0x19000)
  000009a4:  c1d10f37  lui(t5, 0xC1D10000)
  000009a8:  304f0f13  addi(t5, t5, 0x304)
  000009ac:  01eea023  sw(t5, t4, 0)  # [CQ_DEBUG (L1+0x19000)]
  000009b0:  ffb20eb7  lui(t4, 0xFFB20000)  # t4=NOC_TARG_ADDR_LO (NOC0)
  000009b4:  204e8e93  addi(t4, t4, 0x204)  # t4=NOC_STATUS_BASE+0x4 (NOC0+0x204)
  000009b8:  000eab03  lw(s6, t4, 0)  # [NOC_STATUS_BASE+0x4 (NOC0+0x204)]
  000009bc:  ffb30eb7  lui(t4, 0xFFB30000)  # t4=NOC1
  000009c0:  040e8e93  addi(t4, t4, 0x40)  # t4=NOC1+0x40
.Lnoc_ready_15:
  000009c4:  000eaf03  lw(t5, t4, 0)  # [NOC1+0x40]
  000009c8:  fe0f1ee3  bne(t5, zero, .Lnoc_ready_15)  # bne(t5, zero, -4)
  000009cc:  ffb30eb7  lui(t4, 0xFFB30000)  # t4=NOC1
  000009d0:  01ce8e93  addi(t4, t4, 0x1C)  # t4=NOC1+0x1c
  000009d4:  00002f37  lui(t5, 0x2000)  # t5=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  000009d8:  092f0f13  addi(t5, t5, 0x92)  # t5=NOC_CMD_WR_FIELD (L1+0x2092)
  000009dc:  01eea023  sw(t5, t4, 0)  # [NOC1+0x1c], value=NOC_CMD_WR_FIELD (L1+0x2092)
  000009e0:  ffb30eb7  lui(t4, 0xFFB30000)  # t4=NOC1
  000009e4:  006ea023  sw(t1, t4, 0)  # [NOC1], value=COMPLETION_WR_PTR (L1+0x196d0)
  000009e8:  ffb30eb7  lui(t4, 0xFFB30000)  # t4=NOC1
  000009ec:  00ce8e93  addi(t4, t4, 0xC)  # t4=NOC1+0xc
  000009f0:  007ea023  sw(t2, t4, 0)  # [NOC1+0xc], value=HOST_COMPLETION_WR_PTR_OFF
  000009f4:  ffb30eb7  lui(t4, 0xFFB30000)  # t4=NOC1
  000009f8:  010e8e93  addi(t4, t4, 0x10)  # t4=NOC1+0x10
  000009fc:  10000f37  lui(t5, 0x10000000)  # t5=NOC_PCIE_MID
  00000a00:  01eea023  sw(t5, t4, 0)  # [NOC1+0x10], value=NOC_PCIE_MID
  00000a04:  ffb30eb7  lui(t4, 0xFFB30000)  # t4=NOC1
  00000a08:  014e8e93  addi(t4, t4, 0x14)  # t4=NOC1+0x14
  00000a0c:  01000f37  lui(t5, 0x1000000)
  00000a10:  613f0f13  addi(t5, t5, 0x613)  # t5=PCIE_NOC_XY
  00000a14:  01eea023  sw(t5, t4, 0)  # [NOC1+0x14], value=PCIE_NOC_XY
  00000a18:  ffb30eb7  lui(t4, 0xFFB30000)  # t4=NOC1
  00000a1c:  020e8e93  addi(t4, t4, 0x20)  # t4=NOC1+0x20
  00000a20:  01cea023  sw(t3, t4, 0)  # [NOC1+0x20]
  00000a24:  ffb30eb7  lui(t4, 0xFFB30000)  # t4=NOC1
  00000a28:  024e8e93  addi(t4, t4, 0x24)  # t4=NOC1+0x24
  00000a2c:  00000f13  addi(t5, zero, 0)
  00000a30:  01eea023  sw(t5, t4, 0)  # [NOC1+0x24]
  00000a34:  ffb30eb7  lui(t4, 0xFFB30000)  # t4=NOC1
  00000a38:  040e8e93  addi(t4, t4, 0x40)  # t4=NOC1+0x40
  00000a3c:  00100f13  addi(t5, zero, 1)
  00000a40:  01eea023  sw(t5, t4, 0)  # [NOC1+0x40]
  00000a44:  001b0b13  addi(s6, s6, 1)
  00000a48:  00019eb7  lui(t4, 0x19000)  # t4=CQ_DEBUG (L1+0x19000)
  00000a4c:  c1d10f37  lui(t5, 0xC1D10000)
  00000a50:  305f0f13  addi(t5, t5, 0x305)
  00000a54:  01eea023  sw(t5, t4, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000a58:  ffb30eb7  lui(t4, 0xFFB30000)  # t4=NOC1
  00000a5c:  204e8e93  addi(t4, t4, 0x204)  # t4=NOC1+0x204
.Lwr_ack_16:
  00000a60:  000eaf03  lw(t5, t4, 0)  # [NOC1+0x204]
  00000a64:  ff6f6ee3  bltu(t5, s6, .Lwr_ack_16)  # bltu(t5, s6, -4)
  00000a68:  00019eb7  lui(t4, 0x19000)  # t4=CQ_DEBUG (L1+0x19000)
  00000a6c:  c1d10f37  lui(t5, 0xC1D10000)
  00000a70:  306f0f13  addi(t5, t5, 0x306)
  00000a74:  01eea023  sw(t5, t4, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000a78:  00001337  lui(t1, 0x1000)  # t1=STREAM_STRIDE (L1+0x1000)
  00000a7c:  00640433  add(s0, s0, t1)
  00000a80:  0e00006f  jal(zero, release_flush_and_continue)  # jal(zero, 0xE0)
cmd_timestamp:
  00000a84:  00442283  lw(t0, s0, 4)
  00000a88:  00842303  lw(t1, s0, 8)
  00000a8c:  ffb12e37  lui(t3, 0xFFB12000)  # t3=RISCV_DEBUG/RESET+0x2000
  00000a90:  1f0e0e13  addi(t3, t3, 0x1F0)  # t3=RISCV_DEBUG_REG_WALL_CLOCK_L (RISCV_DEBUG/RESET+0x21f0)
  00000a94:  000e2383  lw(t2, t3, 0)  # [RISCV_DEBUG_REG_WALL_CLOCK_L (RISCV_DEBUG/RESET+0x21f0)]
  00000a98:  ffb12eb7  lui(t4, 0xFFB12000)  # t4=RISCV_DEBUG/RESET+0x2000
  00000a9c:  1f8e8e93  addi(t4, t4, 0x1F8)  # t4=RISCV_DEBUG_REG_WALL_CLOCK_H (RISCV_DEBUG/RESET+0x21f8)
  00000aa0:  000eae03  lw(t3, t4, 0)  # [RISCV_DEBUG_REG_WALL_CLOCK_H (RISCV_DEBUG/RESET+0x21f8)]
  00000aa4:  00742023  sw(t2, s0, 0)
  00000aa8:  01c42223  sw(t3, s0, 4)
  00000aac:  00800e93  addi(t4, zero, 8)
  00000ab0:  ffb30f37  lui(t5, 0xFFB30000)  # t5=NOC1
  00000ab4:  040f0f13  addi(t5, t5, 0x40)  # t5=NOC1+0x40
.Lnoc_ready_17:
  00000ab8:  000f2983  lw(s3, t5, 0)  # [NOC1+0x40]
  00000abc:  fe099ee3  bne(s3, zero, .Lnoc_ready_17)  # bne(s3, zero, -4)
  00000ac0:  ffb30f37  lui(t5, 0xFFB30000)  # t5=NOC1
  00000ac4:  01cf0f13  addi(t5, t5, 0x1C)  # t5=NOC1+0x1c
  00000ac8:  000029b7  lui(s3, 0x2000)  # s3=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  00000acc:  09298993  addi(s3, s3, 0x92)  # s3=NOC_CMD_WR_FIELD (L1+0x2092)
  00000ad0:  013f2023  sw(s3, t5, 0)  # [NOC1+0x1c], value=NOC_CMD_WR_FIELD (L1+0x2092)
  00000ad4:  ffb30f37  lui(t5, 0xFFB30000)  # t5=NOC1
  00000ad8:  008f2023  sw(s0, t5, 0)  # [NOC1]
  00000adc:  ffb30f37  lui(t5, 0xFFB30000)  # t5=NOC1
  00000ae0:  00cf0f13  addi(t5, t5, 0xC)  # t5=NOC1+0xc
  00000ae4:  006f2023  sw(t1, t5, 0)  # [NOC1+0xc]
  00000ae8:  ffb30f37  lui(t5, 0xFFB30000)  # t5=NOC1
  00000aec:  010f0f13  addi(t5, t5, 0x10)  # t5=NOC1+0x10
  00000af0:  100009b7  lui(s3, 0x10000000)  # s3=NOC_PCIE_MID
  00000af4:  013f2023  sw(s3, t5, 0)  # [NOC1+0x10], value=NOC_PCIE_MID
  00000af8:  ffb30f37  lui(t5, 0xFFB30000)  # t5=NOC1
  00000afc:  014f0f13  addi(t5, t5, 0x14)  # t5=NOC1+0x14
  00000b00:  005f2023  sw(t0, t5, 0)  # [NOC1+0x14]
  00000b04:  ffb30f37  lui(t5, 0xFFB30000)  # t5=NOC1
  00000b08:  020f0f13  addi(t5, t5, 0x20)  # t5=NOC1+0x20
  00000b0c:  01df2023  sw(t4, t5, 0)  # [NOC1+0x20]
  00000b10:  ffb30f37  lui(t5, 0xFFB30000)  # t5=NOC1
  00000b14:  024f0f13  addi(t5, t5, 0x24)  # t5=NOC1+0x24
  00000b18:  00000993  addi(s3, zero, 0)
  00000b1c:  013f2023  sw(s3, t5, 0)  # [NOC1+0x24]
  00000b20:  ffb30f37  lui(t5, 0xFFB30000)  # t5=NOC1
  00000b24:  040f0f13  addi(t5, t5, 0x40)  # t5=NOC1+0x40
  00000b28:  00100993  addi(s3, zero, 1)
  00000b2c:  013f2023  sw(s3, t5, 0)  # [NOC1+0x40]
  00000b30:  001b0b13  addi(s6, s6, 1)
  00000b34:  ffb30f37  lui(t5, 0xFFB30000)  # t5=NOC1
  00000b38:  204f0f13  addi(t5, t5, 0x204)  # t5=NOC1+0x204
.Lwr_ack_18:
  00000b3c:  000f2983  lw(s3, t5, 0)  # [NOC1+0x204]
  00000b40:  ff69eee3  bltu(s3, s6, .Lwr_ack_18)  # bltu(s3, s6, -4)
  00000b44:  01040413  addi(s0, s0, 0x10)
  00000b48:  0100006f  jal(zero, release_and_continue)  # jal(zero, 0x10)
advance_page:
  00000b4c:  000012b7  lui(t0, 0x1000)  # t0=STREAM_STRIDE (L1+0x1000)
  00000b50:  00540433  add(s0, s0, t0)
  00000b54:  0040006f  jal(zero, release_and_continue)  # jal(zero, 4)
release_and_continue:
  00000b58:  00800f93  addi(t6, zero, 8)
  00000b5c:  0080006f  jal(zero, release_common)  # jal(zero, 8)
release_flush_and_continue:
  00000b60:  00100f93  addi(t6, zero, 1)
release_common:
  00000b64:  000012b7  lui(t0, 0x1000)  # t0=STREAM_STRIDE (L1+0x1000)
  00000b68:  fff28293  addi(t0, t0, -1)  # t0=L1+0xfff
  00000b6c:  00540433  add(s0, s0, t0)
  00000b70:  fffff2b7  lui(t0, 0xFFFFF000)
  00000b74:  00547433  and(s0, s0, t0)
  00000b78:  00040e13  addi(t3, s0, 0)
  00000b7c:  419e0e33  sub(t3, t3, s9)
  00000b80:  00ce5e13  srli(t3, t3, 0xC)
  00000b84:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000b88:  01c28293  addi(t0, t0, 0x1C)  # t0=CQ_DEBUG+0x1c (L1+0x1901c)
  00000b8c:  01c2a023  sw(t3, t0, 0)  # [CQ_DEBUG+0x1c (L1+0x1901c)]
  00000b90:  fffe0e93  addi(t4, t3, -1)
  00000b94:  000e8c63  beq(t4, zero, dispatch_local_pages_done)  # beq(t4, zero, 0x18)
  00000b98:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000b9c:  08428293  addi(t0, t0, 0x84)  # t0=DISPATCH_PAGE_CURSOR (L1+0x19084)
  00000ba0:  0002af03  lw(t5, t0, 0)  # [DISPATCH_PAGE_CURSOR (L1+0x19084)]
  00000ba4:  01df0f33  add(t5, t5, t4)
  00000ba8:  01e2a023  sw(t5, t0, 0)  # [DISPATCH_PAGE_CURSOR (L1+0x19084)]
dispatch_local_pages_done:
  00000bac:  0009a2b7  lui(t0, 0x9A000)  # t0=CMDDAT_Q_BASE (L1.DATA_BUFFER_SPACE+0x63000)
  00000bb0:  00541463  bne(s0, t0, dispatch_no_wrap)  # bne(s0, t0, 8)
  00000bb4:  0001a437  lui(s0, 0x1A000)  # s0=DISPATCH_CB_BASE (L1+0x1a000)
dispatch_no_wrap:
  00000bb8:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000bbc:  08028293  addi(t0, t0, 0x80)  # t0=DISPATCH_RELEASE_PENDING (L1+0x19080)
  00000bc0:  0002ae83  lw(t4, t0, 0)  # [DISPATCH_RELEASE_PENDING (L1+0x19080)]
  00000bc4:  01ce8eb3  add(t4, t4, t3)
  00000bc8:  01d2a023  sw(t4, t0, 0)  # [DISPATCH_RELEASE_PENDING (L1+0x19080)]
  00000bcc:  0ffee263  bltu(t4, t6, release_skip_atomic)  # bltu(t4, t6, 0xE4)
  00000bd0:  000e8e13  addi(t3, t4, 0)
  00000bd4:  0002a023  sw(zero, t0, 0)  # [DISPATCH_RELEASE_PENDING (L1+0x19080)]
  00000bd8:  ffb302b7  lui(t0, 0xFFB30000)  # t0=NOC1
  00000bdc:  20428293  addi(t0, t0, 0x204)  # t0=NOC1+0x204
.Lwr_ack_19:
  00000be0:  0002ae83  lw(t4, t0, 0)  # [NOC1+0x204]
  00000be4:  ff6eeee3  bltu(t4, s6, .Lwr_ack_19)  # bltu(t4, s6, -4)
  00000be8:  0ff0000f  fence()
  00000bec:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000bf0:  09028293  addi(t0, t0, 0x90)  # t0=DISPATCH_RELEASE_VALUE (L1+0x19090)
  00000bf4:  0002ae83  lw(t4, t0, 0)  # [DISPATCH_RELEASE_VALUE (L1+0x19090)]
  00000bf8:  01ce8eb3  add(t4, t4, t3)
  00000bfc:  01d2a023  sw(t4, t0, 0)  # [DISPATCH_RELEASE_VALUE (L1+0x19090)]
  00000c00:  00008337  lui(t1, 0x8000)  # t1=L1+0x8000
  00000c04:  6c030313  addi(t1, t1, 0x6C0)  # t1=CQ_SEM_BASE (L1.KERNEL_CONFIG+0x10)
  00000c08:  00400e13  addi(t3, zero, 4)
  00000c0c:  00019f37  lui(t5, 0x19000)  # t5=CQ_DEBUG (L1+0x19000)
  00000c10:  c1d1f9b7  lui(s3, 0xC1D1F000)
  00000c14:  01098993  addi(s3, s3, 0x10)
  00000c18:  013f2023  sw(s3, t5, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000c1c:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000c20:  040f0f13  addi(t5, t5, 0x40)  # t5=NOC1+0x1040
.Lnoc_ready_20:
  00000c24:  000f2983  lw(s3, t5, 0)  # [NOC1+0x1040]
  00000c28:  fe099ee3  bne(s3, zero, .Lnoc_ready_20)  # bne(s3, zero, -4)
  00000c2c:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000c30:  01cf0f13  addi(t5, t5, 0x1C)  # t5=NOC1+0x101c
  00000c34:  000029b7  lui(s3, 0x2000)  # s3=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  00000c38:  09298993  addi(s3, s3, 0x92)  # s3=NOC_CMD_WR_FIELD (L1+0x2092)
  00000c3c:  013f2023  sw(s3, t5, 0)  # [NOC1+0x101c], value=NOC_CMD_WR_FIELD (L1+0x2092)
  00000c40:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000c44:  005f2023  sw(t0, t5, 0)  # [NOC1+0x1000], value=DISPATCH_RELEASE_VALUE (L1+0x19090)
  00000c48:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000c4c:  00cf0f13  addi(t5, t5, 0xC)  # t5=NOC1+0x100c
  00000c50:  006f2023  sw(t1, t5, 0)  # [NOC1+0x100c], value=CQ_SEM_BASE (L1.KERNEL_CONFIG+0x10)
  00000c54:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000c58:  010f0f13  addi(t5, t5, 0x10)  # t5=NOC1+0x1010
  00000c5c:  00000993  addi(s3, zero, 0)
  00000c60:  013f2023  sw(s3, t5, 0)  # [NOC1+0x1010]
  00000c64:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000c68:  014f0f13  addi(t5, t5, 0x14)  # t5=NOC1+0x1014
  00000c6c:  08e00993  addi(s3, zero, 0x8E)
  00000c70:  013f2023  sw(s3, t5, 0)  # [NOC1+0x1014]
  00000c74:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000c78:  020f0f13  addi(t5, t5, 0x20)  # t5=NOC1+0x1020
  00000c7c:  01cf2023  sw(t3, t5, 0)  # [NOC1+0x1020]
  00000c80:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000c84:  024f0f13  addi(t5, t5, 0x24)  # t5=NOC1+0x1024
  00000c88:  00000993  addi(s3, zero, 0)
  00000c8c:  013f2023  sw(s3, t5, 0)  # [NOC1+0x1024]
  00000c90:  ffb31f37  lui(t5, 0xFFB31000)  # t5=NOC1+0x1000
  00000c94:  040f0f13  addi(t5, t5, 0x40)  # t5=NOC1+0x1040
  00000c98:  00100993  addi(s3, zero, 1)
  00000c9c:  013f2023  sw(s3, t5, 0)  # [NOC1+0x1040]
  00000ca0:  00019f37  lui(t5, 0x19000)  # t5=CQ_DEBUG (L1+0x19000)
  00000ca4:  c1d1f9b7  lui(s3, 0xC1D1F000)
  00000ca8:  01198993  addi(s3, s3, 0x11)
  00000cac:  013f2023  sw(s3, t5, 0)  # [CQ_DEBUG (L1+0x19000)]
release_skip_atomic:
  00000cb0:  bb8ff06f  jal(zero, dispatch_loop)  # jal(zero, -3144)
dispatch_done:
  00000cb4:  0000006f  jal(zero, dispatch_done)  # jal(zero, 0)
```
