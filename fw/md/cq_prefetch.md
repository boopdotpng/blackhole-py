# cq_prefetch

## Summary

| field | value |
| --- | ---: |
| kind | `brisc` |
| base | `0x0` |
| instructions | 323 |
| text bytes | 1292 (`0x50c`) |

## Segments

| label | address | size | flags |
| --- | ---: | ---: | --- |
| `text` | `0x0` | 1292 (`0x50c`) | `RX` |

## Disassembly

```python
; cq_prefetch: blackhole-py firmware

  00000000:  ffb02137  lui(sp, 0xFFB02000)  # sp=LOCAL_RAM_END+1 (RISC_LOCAL_RAM_END+1)
  00000004:  ff010113  addi(sp, sp, -16)  # sp=BRISC_STACK_TOP (RISC_LOCAL_RAM+0x1ff0)
  00000008:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  0000000c:  c1010337  lui(t1, 0xC1010000)
  00000010:  00130313  addi(t1, t1, 1)
  00000014:  0062a023  sw(t1, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000018:  000082b7  lui(t0, 0x8000)  # t0=L1+0x8000
  0000001c:  6c028293  addi(t0, t0, 0x6C0)  # t0=CQ_SEM_BASE (L1.KERNEL_CONFIG+0x10)
  00000020:  08000313  addi(t1, zero, 0x80)
  00000024:  0062a023  sw(t1, t0, 0)  # [CQ_SEM_BASE (L1.KERNEL_CONFIG+0x10)]
  00000028:  0001a437  lui(s0, 0x1A000)  # s0=DISPATCH_CB_BASE (L1+0x1a000)
  0000002c:  84040413  addi(s0, s0, -1984)  # s0=PREFETCH_Q_BASE (L1+0x19840)
  00000030:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000034:  6c428293  addi(t0, t0, 0x6C4)  # t0=PREFETCH_Q_PCIE_RD (L1+0x196c4)
  00000038:  0002a483  lw(s1, t0, 0)  # [PREFETCH_Q_PCIE_RD (L1+0x196c4)]
  0000003c:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  00000040:  0a028293  addi(t0, t0, 0xA0)  # t0=PREFETCH_PCIE_BASE (L1+0x190a0)
  00000044:  0092a023  sw(s1, t0, 0)  # [PREFETCH_PCIE_BASE (L1+0x190a0)]
  00000048:  040002b7  lui(t0, 0x4000000)
  0000004c:  005482b3  add(t0, s1, t0)
  00000050:  00019337  lui(t1, 0x19000)  # t1=CQ_DEBUG (L1+0x19000)
  00000054:  0a430313  addi(t1, t1, 0xA4)  # t1=PREFETCH_PCIE_END (L1+0x190a4)
  00000058:  00532023  sw(t0, t1, 0)  # [PREFETCH_PCIE_END (L1+0x190a4)]
  0000005c:  0001a937  lui(s2, 0x1A000)  # s2=DISPATCH_CB_BASE (L1+0x1a000)
  00000060:  00000c13  addi(s8, zero, 0)
  00000064:  ffb202b7  lui(t0, 0xFFB20000)  # t0=NOC_TARG_ADDR_LO (NOC0)
  00000068:  20828293  addi(t0, t0, 0x208)  # t0=NOC_STATUS_BASE+0x8 (NOC0+0x208)
  0000006c:  0002aa03  lw(s4, t0, 0)  # [NOC_STATUS_BASE+0x8 (NOC0+0x208)]
  00000070:  ffb202b7  lui(t0, 0xFFB20000)  # t0=NOC_TARG_ADDR_LO (NOC0)
  00000074:  20428293  addi(t0, t0, 0x204)  # t0=NOC_STATUS_BASE+0x4 (NOC0+0x204)
  00000078:  0002aa83  lw(s5, t0, 0)  # [NOC_STATUS_BASE+0x4 (NOC0+0x204)]
  0000007c:  ffb202b7  lui(t0, 0xFFB20000)  # t0=NOC_TARG_ADDR_LO (NOC0)
  00000080:  20028293  addi(t0, t0, 0x200)  # t0=NOC_STATUS_BASE (NOC0+0x200)
  00000084:  0002ab83  lw(s7, t0, 0)  # [NOC_STATUS_BASE (NOC0+0x200)]
prefetch_loop:
  00000088:  000192b7  lui(t0, 0x19000)  # t0=CQ_DEBUG (L1+0x19000)
  0000008c:  c1010337  lui(t1, 0xC1010000)
  00000090:  00230313  addi(t1, t1, 2)
  00000094:  0062a023  sw(t1, t0, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000098:  00045283  lhu(t0, s0, 0)  # [PREFETCH_Q_BASE (L1+0x19840)]
  0000009c:  fe0286e3  beq(t0, zero, prefetch_loop)  # beq(t0, zero, -20)
  000000a0:  00008337  lui(t1, 0x8000)  # t1=L1+0x8000
  000000a4:  fff30313  addi(t1, t1, -1)  # t1=L1+0x7fff
  000000a8:  0062f2b3  and(t0, t0, t1)
  000000ac:  fc028ee3  beq(t0, zero, prefetch_loop)  # beq(t0, zero, -36)
  000000b0:  00429293  slli(t0, t0, 4)
  000000b4:  0009a337  lui(t1, 0x9A000)  # t1=CMDDAT_Q_BASE (L1.DATA_BUFFER_SPACE+0x63000)
  000000b8:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000000bc:  00438393  addi(t2, t2, 4)  # t2=CQ_DEBUG+0x4 (L1+0x19004)
  000000c0:  0053a023  sw(t0, t2, 0)  # [CQ_DEBUG+0x4 (L1+0x19004)]
  000000c4:  00048c93  addi(s9, s1, 0)
  000000c8:  00030d13  addi(s10, t1, 0)  # s10=CMDDAT_Q_BASE (L1.DATA_BUFFER_SPACE+0x63000)
  000000cc:  00028d93  addi(s11, t0, 0)
prefetch_read_loop:
  000000d0:  0c0d8c63  beq(s11, zero, prefetch_read_done)  # beq(s11, zero, 0xD8)
  000000d4:  00004eb7  lui(t4, 0x4000)  # t4=NOC_MAX_BURST_SIZE (L1+0x4000)
  000000d8:  01bee663  bltu(t4, s11, prefetch_read_full_burst)  # bltu(t4, s11, 0xC)
  000000dc:  000d8f13  addi(t5, s11, 0)
  000000e0:  0080006f  jal(zero, prefetch_read_issue)  # jal(zero, 8)
prefetch_read_full_burst:
  000000e4:  000e8f13  addi(t5, t4, 0)  # t5=NOC_MAX_BURST_SIZE (L1+0x4000)
prefetch_read_issue:
  000000e8:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  000000ec:  84038393  addi(t2, t2, -1984)  # t2=NOC0+0x840
.Lnoc_ready_1:
  000000f0:  0003ae03  lw(t3, t2, 0)  # [NOC0+0x840]
  000000f4:  fe0e1ee3  bne(t3, zero, .Lnoc_ready_1)  # bne(t3, zero, -4)
  000000f8:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  000000fc:  81c38393  addi(t2, t2, -2020)  # t2=NOC0+0x81c
  00000100:  00002e37  lui(t3, 0x2000)  # t3=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  00000104:  090e0e13  addi(t3, t3, 0x90)  # t3=NOC_CMD_RD_FIELD (L1+0x2090)
  00000108:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x81c], value=NOC_CMD_RD_FIELD (L1+0x2090)
  0000010c:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00000110:  80c38393  addi(t2, t2, -2036)  # t2=NOC0+0x80c
  00000114:  01a3a023  sw(s10, t2, 0)  # [NOC0+0x80c], value=CMDDAT_Q_BASE (L1.DATA_BUFFER_SPACE+0x63000)
  00000118:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  0000011c:  81038393  addi(t2, t2, -2032)  # t2=NOC0+0x810
  00000120:  00000e13  addi(t3, zero, 0)
  00000124:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x810]
  00000128:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  0000012c:  81438393  addi(t2, t2, -2028)  # t2=NOC0+0x814
  00000130:  08e00e13  addi(t3, zero, 0x8E)
  00000134:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x814]
  00000138:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  0000013c:  80038393  addi(t2, t2, -2048)  # t2=NOC0+0x800
  00000140:  0193a023  sw(s9, t2, 0)  # [NOC0+0x800]
  00000144:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00000148:  80438393  addi(t2, t2, -2044)  # t2=NOC0+0x804
  0000014c:  10000e37  lui(t3, 0x10000000)  # t3=NOC_PCIE_MID
  00000150:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x804], value=NOC_PCIE_MID
  00000154:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00000158:  80838393  addi(t2, t2, -2040)  # t2=NOC0+0x808
  0000015c:  01000e37  lui(t3, 0x1000000)
  00000160:  613e0e13  addi(t3, t3, 0x613)  # t3=PCIE_NOC_XY
  00000164:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x808], value=PCIE_NOC_XY
  00000168:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  0000016c:  82038393  addi(t2, t2, -2016)  # t2=NOC0+0x820
  00000170:  01e3a023  sw(t5, t2, 0)  # [NOC0+0x820], value=NOC_MAX_BURST_SIZE (L1+0x4000)
  00000174:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00000178:  82438393  addi(t2, t2, -2012)  # t2=NOC0+0x824
  0000017c:  00000e13  addi(t3, zero, 0)
  00000180:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x824]
  00000184:  ffb213b7  lui(t2, 0xFFB21000)  # t2=NOC0+0x1000
  00000188:  84038393  addi(t2, t2, -1984)  # t2=NOC0+0x840
  0000018c:  00100e13  addi(t3, zero, 1)
  00000190:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x840]
  00000194:  001a0a13  addi(s4, s4, 1)
  00000198:  01ec8cb3  add(s9, s9, t5)
  0000019c:  01ed0d33  add(s10, s10, t5)
  000001a0:  41ed8db3  sub(s11, s11, t5)
  000001a4:  f2dff06f  jal(zero, prefetch_read_loop)  # jal(zero, -212)
prefetch_read_done:
  000001a8:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  000001ac:  20838393  addi(t2, t2, 0x208)  # t2=NOC_STATUS_BASE+0x8 (NOC0+0x208)
prefetch_read_barrier:
  000001b0:  0003ae03  lw(t3, t2, 0)  # [NOC_STATUS_BASE+0x8 (NOC0+0x208)]
  000001b4:  ff4e6ee3  bltu(t3, s4, prefetch_read_barrier)  # bltu(t3, s4, -4)
  000001b8:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000001bc:  c1010e37  lui(t3, 0xC1010000)
  000001c0:  003e0e13  addi(t3, t3, 3)
  000001c4:  01c3a023  sw(t3, t2, 0)  # [CQ_DEBUG (L1+0x19000)]
  000001c8:  00041023  sh(zero, s0, 0)  # [PREFETCH_Q_BASE (L1+0x19840)]
  000001cc:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000001d0:  6c038393  addi(t2, t2, 0x6C0)  # t2=PREFETCH_Q_RD_PTR (L1+0x196c0)
  000001d4:  0083a023  sw(s0, t2, 0)  # [PREFETCH_Q_RD_PTR (L1+0x196c0)], value=PREFETCH_Q_BASE (L1+0x19840)
  000001d8:  005484b3  add(s1, s1, t0)
  000001dc:  00019e37  lui(t3, 0x19000)  # t3=CQ_DEBUG (L1+0x19000)
  000001e0:  0a4e0e13  addi(t3, t3, 0xA4)  # t3=PREFETCH_PCIE_END (L1+0x190a4)
  000001e4:  000e2383  lw(t2, t3, 0)  # [PREFETCH_PCIE_END (L1+0x190a4)]
  000001e8:  0074e863  bltu(s1, t2, prefetch_no_pcie_wrap)  # bltu(s1, t2, 0x10)
  000001ec:  00019e37  lui(t3, 0x19000)  # t3=CQ_DEBUG (L1+0x19000)
  000001f0:  0a0e0e13  addi(t3, t3, 0xA0)  # t3=PREFETCH_PCIE_BASE (L1+0x190a0)
  000001f4:  000e2483  lw(s1, t3, 0)  # [PREFETCH_PCIE_BASE (L1+0x190a0)]
prefetch_no_pcie_wrap:
  000001f8:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000001fc:  6c438393  addi(t2, t2, 0x6C4)  # t2=PREFETCH_Q_PCIE_RD (L1+0x196c4)
  00000200:  0093a023  sw(s1, t2, 0)  # [PREFETCH_Q_PCIE_RD (L1+0x196c4)]
  00000204:  00440413  addi(s0, s0, 4)  # s0=PREFETCH_Q_BASE+0x4 (L1+0x19844)
  00000208:  0001a3b7  lui(t2, 0x1A000)  # t2=DISPATCH_CB_BASE (L1+0x1a000)
  0000020c:  43c38393  addi(t2, t2, 0x43C)  # t2=PREFETCH_Q_END (L1+0x1a43c)
  00000210:  00741663  bne(s0, t2, prefetch_no_q_wrap)  # bne(s0, t2, 0xC)
  00000214:  0001a437  lui(s0, 0x1A000)  # s0=DISPATCH_CB_BASE (L1+0x1a000)
  00000218:  84040413  addi(s0, s0, -1984)  # s0=PREFETCH_Q_BASE (L1+0x19840)
prefetch_no_q_wrap:
  0000021c:  0009a337  lui(t1, 0x9A000)  # t1=CMDDAT_Q_BASE (L1.DATA_BUFFER_SPACE+0x63000)
  00000220:  00034383  lbu(t2, t1, 0)  # [CMDDAT_Q_BASE (L1.DATA_BUFFER_SPACE+0x63000)]
  00000224:  00019e37  lui(t3, 0x19000)  # t3=CQ_DEBUG (L1+0x19000)
  00000228:  008e0e13  addi(t3, t3, 8)  # t3=CQ_DEBUG+0x8 (L1+0x19008)
  0000022c:  007e2023  sw(t2, t3, 0)  # [CQ_DEBUG+0x8 (L1+0x19008)]
  00000230:  00500e13  addi(t3, zero, 5)
  00000234:  03c38463  beq(t2, t3, prefetch_relay_inline)  # beq(t2, t3, 0x28)
  00000238:  00600e13  addi(t3, zero, 6)
  0000023c:  03c38063  beq(t2, t3, prefetch_relay_inline)  # beq(t2, t3, 0x20)
  00000240:  00800e13  addi(t3, zero, 8)
  00000244:  01c38c63  beq(t2, t3, prefetch_relay_inline)  # beq(t2, t3, 0x18)
  00000248:  00900e13  addi(t3, zero, 9)
  0000024c:  e3c38ee3  beq(t2, t3, prefetch_loop)  # beq(t2, t3, -452)
  00000250:  00b00e13  addi(t3, zero, 0xB)
  00000254:  2bc38263  beq(t2, t3, prefetch_done)  # beq(t2, t3, 0x2A4)
  00000258:  28c0006f  jal(zero, prefetch_bad_cmd)  # jal(zero, 0x28C)
prefetch_relay_inline:
  0000025c:  00432283  lw(t0, t1, 4)  # [L1.DATA_BUFFER_SPACE+0x63004]
  00000260:  00028b13  addi(s6, t0, 0)
  00000264:  01030313  addi(t1, t1, 0x10)  # t1=L1.DATA_BUFFER_SPACE+0x63010
  00000268:  000013b7  lui(t2, 0x1000)  # t2=STREAM_STRIDE (L1+0x1000)
  0000026c:  fff38393  addi(t2, t2, -1)  # t2=L1+0xfff
  00000270:  007283b3  add(t2, t0, t2)
  00000274:  00c3d393  srli(t2, t2, 0xC)
  00000278:  00038993  addi(s3, t2, 0)
  0000027c:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  00000280:  00c38393  addi(t2, t2, 0xC)  # t2=CQ_DEBUG+0xc (L1+0x1900c)
  00000284:  0133a023  sw(s3, t2, 0)  # [CQ_DEBUG+0xc (L1+0x1900c)]
  00000288:  00008e37  lui(t3, 0x8000)  # t3=L1+0x8000
  0000028c:  6c0e0e13  addi(t3, t3, 0x6C0)  # t3=CQ_SEM_BASE (L1.KERNEL_CONFIG+0x10)
.Lsem_wait_2:
  00000290:  000e2283  lw(t0, t3, 0)  # [CQ_SEM_BASE (L1.KERNEL_CONFIG+0x10)]
  00000294:  018282b3  add(t0, t0, s8)
  00000298:  ff32ece3  bltu(t0, s3, .Lsem_wait_2)  # bltu(t0, s3, -8)
  0000029c:  413c0c33  sub(s8, s8, s3)
  000002a0:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000002a4:  c1010e37  lui(t3, 0xC1010000)
  000002a8:  004e0e13  addi(t3, t3, 4)
  000002ac:  01c3a023  sw(t3, t2, 0)  # [CQ_DEBUG (L1+0x19000)]
  000002b0:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000002b4:  01038393  addi(t2, t2, 0x10)  # t2=CQ_DEBUG+0x10 (L1+0x19010)
  000002b8:  0123a023  sw(s2, t2, 0)  # [CQ_DEBUG+0x10 (L1+0x19010)], value=DISPATCH_CB_BASE (L1+0x1a000)
  000002bc:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000002c0:  c1010e37  lui(t3, 0xC1010000)
  000002c4:  005e0e13  addi(t3, t3, 5)
  000002c8:  01c3a023  sw(t3, t2, 0)  # [CQ_DEBUG (L1+0x19000)]
  000002cc:  00030c93  addi(s9, t1, 0)  # s9=L1.DATA_BUFFER_SPACE+0x63010
  000002d0:  00090d13  addi(s10, s2, 0)  # s10=DISPATCH_CB_BASE (L1+0x1a000)
  000002d4:  000b0d93  addi(s11, s6, 0)
prefetch_write_loop:
  000002d8:  0e0d8063  beq(s11, zero, prefetch_write_done)  # beq(s11, zero, 0xE0)
  000002dc:  00004eb7  lui(t4, 0x4000)  # t4=NOC_MAX_BURST_SIZE (L1+0x4000)
  000002e0:  01bee663  bltu(t4, s11, prefetch_write_full_burst)  # bltu(t4, s11, 0xC)
  000002e4:  000d8293  addi(t0, s11, 0)
  000002e8:  0080006f  jal(zero, prefetch_write_size_ready)  # jal(zero, 8)
prefetch_write_full_burst:
  000002ec:  000e8293  addi(t0, t4, 0)  # t0=NOC_MAX_BURST_SIZE (L1+0x4000)
prefetch_write_size_ready:
  000002f0:  0009aeb7  lui(t4, 0x9A000)  # t4=CMDDAT_Q_BASE (L1.DATA_BUFFER_SPACE+0x63000)
  000002f4:  41ae8eb3  sub(t4, t4, s10)
  000002f8:  005ee463  bltu(t4, t0, prefetch_write_trim_to_end)  # bltu(t4, t0, 8)
  000002fc:  0080006f  jal(zero, prefetch_write_issue)  # jal(zero, 8)
prefetch_write_trim_to_end:
  00000300:  000e8293  addi(t0, t4, 0)
prefetch_write_issue:
  00000304:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00000308:  04038393  addi(t2, t2, 0x40)  # t2=NOC_CMD_CTRL (NOC0+0x40)
.Lnoc_ready_3:
  0000030c:  0003ae03  lw(t3, t2, 0)  # [NOC_CMD_CTRL (NOC0+0x40)]
  00000310:  fe0e1ee3  bne(t3, zero, .Lnoc_ready_3)  # bne(t3, zero, -4)
  00000314:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00000318:  01c38393  addi(t2, t2, 0x1C)  # t2=NOC_CTRL (NOC0+0x1c)
  0000031c:  00002e37  lui(t3, 0x2000)  # t3=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  00000320:  092e0e13  addi(t3, t3, 0x92)  # t3=NOC_CMD_WR_FIELD (L1+0x2092)
  00000324:  01c3a023  sw(t3, t2, 0)  # [NOC_CTRL (NOC0+0x1c)], value=NOC_CMD_WR_FIELD (L1+0x2092)
  00000328:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  0000032c:  0193a023  sw(s9, t2, 0)  # [NOC_TARG_ADDR_LO (NOC0)], value=L1.DATA_BUFFER_SPACE+0x63010
  00000330:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00000334:  00c38393  addi(t2, t2, 0xC)  # t2=NOC_RET_ADDR_LO (NOC0+0xc)
  00000338:  01a3a023  sw(s10, t2, 0)  # [NOC_RET_ADDR_LO (NOC0+0xc)], value=DISPATCH_CB_BASE (L1+0x1a000)
  0000033c:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00000340:  01038393  addi(t2, t2, 0x10)  # t2=NOC_RET_ADDR_MID (NOC0+0x10)
  00000344:  00000e13  addi(t3, zero, 0)
  00000348:  01c3a023  sw(t3, t2, 0)  # [NOC_RET_ADDR_MID (NOC0+0x10)]
  0000034c:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00000350:  01438393  addi(t2, t2, 0x14)  # t2=NOC_RET_ADDR_COORDINATE (NOC0+0x14)
  00000354:  0ce00e13  addi(t3, zero, 0xCE)
  00000358:  01c3a023  sw(t3, t2, 0)  # [NOC_RET_ADDR_COORDINATE (NOC0+0x14)]
  0000035c:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00000360:  02038393  addi(t2, t2, 0x20)  # t2=NOC_AT_LEN_BE (NOC0+0x20)
  00000364:  0053a023  sw(t0, t2, 0)  # [NOC_AT_LEN_BE (NOC0+0x20)]
  00000368:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  0000036c:  02438393  addi(t2, t2, 0x24)  # t2=NOC_AT_LEN_BE_1 (NOC0+0x24)
  00000370:  00000e13  addi(t3, zero, 0)
  00000374:  01c3a023  sw(t3, t2, 0)  # [NOC_AT_LEN_BE_1 (NOC0+0x24)]
  00000378:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  0000037c:  04038393  addi(t2, t2, 0x40)  # t2=NOC_CMD_CTRL (NOC0+0x40)
  00000380:  00100e13  addi(t3, zero, 1)
  00000384:  01c3a023  sw(t3, t2, 0)  # [NOC_CMD_CTRL (NOC0+0x40)]
  00000388:  001a8a93  addi(s5, s5, 1)
  0000038c:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  00000390:  20438393  addi(t2, t2, 0x204)  # t2=NOC_STATUS_BASE+0x4 (NOC0+0x204)
.Lwr_ack_4:
  00000394:  0003ae03  lw(t3, t2, 0)  # [NOC_STATUS_BASE+0x4 (NOC0+0x204)]
  00000398:  ff5e6ee3  bltu(t3, s5, .Lwr_ack_4)  # bltu(t3, s5, -4)
  0000039c:  005c8cb3  add(s9, s9, t0)
  000003a0:  005d0d33  add(s10, s10, t0)
  000003a4:  405d8db3  sub(s11, s11, t0)
  000003a8:  0009aeb7  lui(t4, 0x9A000)  # t4=CMDDAT_Q_BASE (L1.DATA_BUFFER_SPACE+0x63000)
  000003ac:  01dd1463  bne(s10, t4, prefetch_write_no_wrap)  # bne(s10, t4, 8)
  000003b0:  0001ad37  lui(s10, 0x1A000)  # s10=DISPATCH_CB_BASE (L1+0x1a000)
prefetch_write_no_wrap:
  000003b4:  f25ff06f  jal(zero, prefetch_write_loop)  # jal(zero, -220)
prefetch_write_done:
  000003b8:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000003bc:  c1010e37  lui(t3, 0xC1010000)
  000003c0:  006e0e13  addi(t3, t3, 6)
  000003c4:  01c3a023  sw(t3, t2, 0)  # [CQ_DEBUG (L1+0x19000)]
  000003c8:  00098293  addi(t0, s3, 0)
  000003cc:  00c29293  slli(t0, t0, 0xC)
  000003d0:  00590933  add(s2, s2, t0)
  000003d4:  0009a337  lui(t1, 0x9A000)  # t1=CMDDAT_Q_BASE (L1.DATA_BUFFER_SPACE+0x63000)
  000003d8:  00696663  bltu(s2, t1, prefetch_no_cb_wrap)  # bltu(s2, t1, 0xC)
  000003dc:  00080eb7  lui(t4, 0x80000)  # t4=L1.DATA_BUFFER_SPACE+0x49000
  000003e0:  41d90933  sub(s2, s2, t4)
prefetch_no_cb_wrap:
  000003e4:  00008337  lui(t1, 0x8000)  # t1=L1+0x8000
  000003e8:  6c030313  addi(t1, t1, 0x6C0)  # t1=CQ_SEM_BASE (L1.KERNEL_CONFIG+0x10)
  000003ec:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000003f0:  c1010e37  lui(t3, 0xC1010000)
  000003f4:  007e0e13  addi(t3, t3, 7)
  000003f8:  01c3a023  sw(t3, t2, 0)  # [CQ_DEBUG (L1+0x19000)]
  000003fc:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  00000400:  84038393  addi(t2, t2, -1984)  # t2=NOC0+0x1840
.Lnoc_ready_5:
  00000404:  0003ae03  lw(t3, t2, 0)  # [NOC0+0x1840]
  00000408:  fe0e1ee3  bne(t3, zero, .Lnoc_ready_5)  # bne(t3, zero, -4)
  0000040c:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  00000410:  80c38393  addi(t2, t2, -2036)  # t2=NOC0+0x180c
  00000414:  00400e13  addi(t3, zero, 4)
  00000418:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x180c]
  0000041c:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  00000420:  81038393  addi(t2, t2, -2032)  # t2=NOC0+0x1810
  00000424:  00000e13  addi(t3, zero, 0)
  00000428:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x1810]
  0000042c:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  00000430:  81438393  addi(t2, t2, -2028)  # t2=NOC0+0x1814
  00000434:  08e00e13  addi(t3, zero, 0x8E)
  00000438:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x1814]
  0000043c:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  00000440:  80038393  addi(t2, t2, -2048)  # t2=NOC0+0x1800
  00000444:  0063a023  sw(t1, t2, 0)  # [NOC0+0x1800], value=CQ_SEM_BASE (L1.KERNEL_CONFIG+0x10)
  00000448:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  0000044c:  80438393  addi(t2, t2, -2044)  # t2=NOC0+0x1804
  00000450:  00000e13  addi(t3, zero, 0)
  00000454:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x1804]
  00000458:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  0000045c:  80838393  addi(t2, t2, -2040)  # t2=NOC0+0x1808
  00000460:  0ce00e13  addi(t3, zero, 0xCE)
  00000464:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x1808]
  00000468:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  0000046c:  81c38393  addi(t2, t2, -2020)  # t2=NOC0+0x181c
  00000470:  00002e37  lui(t3, 0x2000)  # t3=NOC_CMD_STATIC_VC_1 (L1+0x2000)
  00000474:  091e0e13  addi(t3, t3, 0x91)  # t3=NOC_CMD_AT_INC_FIELD (L1+0x2091)
  00000478:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x181c], value=NOC_CMD_AT_INC_FIELD (L1+0x2091)
  0000047c:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  00000480:  82038393  addi(t2, t2, -2016)  # t2=NOC0+0x1820
  00000484:  00001e37  lui(t3, 0x1000)  # t3=STREAM_STRIDE (L1+0x1000)
  00000488:  07ce0e13  addi(t3, t3, 0x7C)  # t3=NOC_AT_INCR_GET (L1+0x107c)
  0000048c:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x1820], value=NOC_AT_INCR_GET (L1+0x107c)
  00000490:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  00000494:  82438393  addi(t2, t2, -2012)  # t2=NOC0+0x1824
  00000498:  00000e13  addi(t3, zero, 0)
  0000049c:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x1824]
  000004a0:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  000004a4:  82838393  addi(t2, t2, -2008)  # t2=NOC0+0x1828
  000004a8:  0133a023  sw(s3, t2, 0)  # [NOC0+0x1828]
  000004ac:  ffb223b7  lui(t2, 0xFFB22000)  # t2=NOC0+0x2000
  000004b0:  84038393  addi(t2, t2, -1984)  # t2=NOC0+0x1840
  000004b4:  00100e13  addi(t3, zero, 1)
  000004b8:  01c3a023  sw(t3, t2, 0)  # [NOC0+0x1840]
  000004bc:  001b8b93  addi(s7, s7, 1)
  000004c0:  ffb203b7  lui(t2, 0xFFB20000)  # t2=NOC_TARG_ADDR_LO (NOC0)
  000004c4:  20038393  addi(t2, t2, 0x200)  # t2=NOC_STATUS_BASE (NOC0+0x200)
.Latomic_resp_6:
  000004c8:  0003ae03  lw(t3, t2, 0)  # [NOC_STATUS_BASE (NOC0+0x200)]
  000004cc:  ff7e6ee3  bltu(t3, s7, .Latomic_resp_6)  # bltu(t3, s7, -4)
  000004d0:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000004d4:  c1010e37  lui(t3, 0xC1010000)
  000004d8:  008e0e13  addi(t3, t3, 8)
  000004dc:  01c3a023  sw(t3, t2, 0)  # [CQ_DEBUG (L1+0x19000)]
  000004e0:  ba9ff06f  jal(zero, prefetch_loop)  # jal(zero, -1112)
prefetch_bad_cmd:
  000004e4:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000004e8:  c1010e37  lui(t3, 0xC1010000)
  000004ec:  0eee0e13  addi(t3, t3, 0xEE)
  000004f0:  01c3a023  sw(t3, t2, 0)  # [CQ_DEBUG (L1+0x19000)]
  000004f4:  ff1ff06f  jal(zero, prefetch_bad_cmd)  # jal(zero, -16)
prefetch_done:
  000004f8:  000193b7  lui(t2, 0x19000)  # t2=CQ_DEBUG (L1+0x19000)
  000004fc:  c1010e37  lui(t3, 0xC1010000)
  00000500:  0ffe0e13  addi(t3, t3, 0xFF)
  00000504:  01c3a023  sw(t3, t2, 0)  # [CQ_DEBUG (L1+0x19000)]
  00000508:  ff1ff06f  jal(zero, prefetch_done)  # jal(zero, -16)
```
