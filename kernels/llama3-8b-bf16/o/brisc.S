# llama3 8b-bf16 decode: o, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_context_decode_token, 0x784=e2e_l0_q, 0x788=e2e_x_b, 0x78c=e2e_x_a, 0x11880=e2e_q_compact, 0x11884=e2e_l0_q_row_start, 0x11888=dense_start, 0x1188c=e2e_l0_q_rows, 0x11890=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
      8: 00012537  lui          x10, 0x00012  # x10 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
      c: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00012000
     10: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     14: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: 248000ef  jal          x1, 0x00000264  # target 0x00000264; x1 = 0x00000020
     20: 260000ef  jal          x1, 0x00000280  # target 0x00000280; x1 = 0x00000024
     24: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     28: 274000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x0000002c
     2c: 000a8213  addi         x4, x21, 0
     30: 000b0293  addi         x5, x22, 0
     34: 00020f93  addi         x31, x4, 0
     38: 00028f13  addi         x30, x5, 0
     3c: 00017eb7  lui          x29, 0x00017  # x29 = 0x00017000
     40: 2e0000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000044
     44: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     48: 254000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x0000004c
     4c: 000a8213  addi         x4, x21, 0
     50: 000b0293  addi         x5, x22, 0
     54: 00020f93  addi         x31, x4, 0
     58: 00028f13  addi         x30, x5, 0
     5c: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
     60: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00017800
     64: 2bc000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000068
     68: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     6c: 230000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x00000070
     70: 000a8213  addi         x4, x21, 0
     74: 000b0293  addi         x5, x22, 0
     78: 00020f93  addi         x31, x4, 0
     7c: 00028f13  addi         x30, x5, 0
     80: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
     84: 29c000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000088
     88: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     8c: 210000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 00019eb7  lui          x29, 0x00019  # x29 = 0x00019000
     a4: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00018800
     a8: 278000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x000000ac
     ac: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     b0: 314000ef  jal          x1, 0x000003c4  # target 0x000003c4; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
     c8: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00019800
     cc: 254000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x000000d0
     d0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     d4: 2f0000ef  jal          x1, 0x000003c4  # target 0x000003c4; x1 = 0x000000d8
     d8: 000a8213  addi         x4, x21, 0
     dc: 000b0293  addi         x5, x22, 0
     e0: 00020f93  addi         x31, x4, 0
     e4: 00028f13  addi         x30, x5, 0
     e8: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
     ec: 234000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x000000f0
     f0: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     f4: 2d0000ef  jal          x1, 0x000003c4  # target 0x000003c4; x1 = 0x000000f8
     f8: 000a8213  addi         x4, x21, 0
     fc: 000b0293  addi         x5, x22, 0
    100: 00020f93  addi         x31, x4, 0
    104: 00028f13  addi         x30, x5, 0
    108: 0001beb7  lui          x29, 0x0001b  # x29 = 0x0001b000
    10c: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001a800
    110: 210000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000114
    114: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    118: 2ac000ef  jal          x1, 0x000003c4  # target 0x000003c4; x1 = 0x0000011c
    11c: 000a8213  addi         x4, x21, 0
    120: 000b0293  addi         x5, x22, 0
    124: 00020f93  addi         x31, x4, 0
    128: 00028f13  addi         x30, x5, 0
    12c: 0001beb7  lui          x29, 0x0001b  # x29 = 0x0001b000
    130: 1f0000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000134
    134: 14c000ef  jal          x1, 0x00000280  # target 0x00000280; x1 = 0x00000138
    138: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    13c: 88c28293  addi         x5, x5, -1908  # x5 = 0x0001188c
    140: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0001188c
    144: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    148: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x00000784
    14c: ff82f293  andi         x5, x5, -8
    150: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    154: 88448493  addi         x9, x9, -1916  # x9 = 0x00011884
    158: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x00011884
    15c: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    160: 028383b3  mul          x7, x7, x8
    164: 0073f313  andi         x6, x7, 7
    168: 0033d393  srli         x7, x7, 3
    16c: 00b39393  slli         x7, x7, 11
    170: 007282b3  add          x5, x5, x7
    174: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    178: 00020413  addi         x8, x4, 0
loc_17c:
    17c: 0e83f263  bgeu         x7, x8, 0x00000260  # target 0x00000260
    180: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    184: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    188: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_18c:
    18c: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    190: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    194: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    198: 40a485b3  sub          x11, x9, x10
    19c: 01059593  slli         x11, x11, 16
    1a0: 0105d593  srli         x11, x11, 16
    1a4: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    1a8: 40b60633  sub          x12, x12, x11
    1ac: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    1b0: 00d67663  bgeu         x12, x13, 0x000001bc  # target 0x000001bc
    1b4: 0ff0000f  fence        0xf, 0xf
    1b8: fd5ff06f  jal          x0, 0x0000018c  # target 0x0000018c
loc_1bc:
    1bc: 0ff0000f  fence        0xf, 0xf
    1c0: 0a4000ef  jal          x1, 0x00000264  # target 0x00000264; x1 = 0x000001c4
    1c4: 0bc000ef  jal          x1, 0x00000280  # target 0x00000280; x1 = 0x000001c8
    1c8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1cc: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    1d0: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    1d4: 00028f93  addi         x31, x5, 0
    1d8: 00030f13  addi         x30, x6, 0
    1dc: 00048e93  addi         x29, x9, 0
    1e0: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    1e4: 264000ef  jal          x1, 0x00000448  # target 0x00000448; x1 = 0x000001e8
    1e8: 000f8293  addi         x5, x31, 0
    1ec: 000f0313  addi         x6, x30, 0
    1f0: 090000ef  jal          x1, 0x00000280  # target 0x00000280; x1 = 0x000001f4
    1f4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    1f8: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    1fc: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    200: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    204: 00a484b3  add          x9, x9, x10
    208: 000165b7  lui          x11, 0x00016  # x11 = 0x00016000
    20c: 00b4e663  bltu         x9, x11, 0x00000218  # target 0x00000218
    210: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    214: 40c484b3  sub          x9, x9, x12
loc_218:
    218: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    21c: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    220: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    224: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    228: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    22c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    230: 00448493  addi         x9, x9, 4
    234: 01049493  slli         x9, x9, 16
    238: 0104d493  srli         x9, x9, 16
    23c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    240: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    244: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    248: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    24c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    250: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    254: 0ff0000f  fence        0xf, 0xf
    258: 00138393  addi         x7, x7, 1
    25c: f21ff06f  jal          x0, 0x0000017c  # target 0x0000017c
loc_260:
    260: 3100006f  jal          x0, 0x00000570  # target 0x00000570
loc_264:
    264: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    268: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    26c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    270: 000a0463  beq          x20, x0, 0x00000278  # target 0x00000278
    274: ff1ff06f  jal          x0, 0x00000264  # target 0x00000264
loc_278:
    278: 0ff0000f  fence        0xf, 0xf
    27c: 00008067  jalr         x0, 0(x1)
loc_280:
    280: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    284: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    288: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    28c: 000a0463  beq          x20, x0, 0x00000294  # target 0x00000294
    290: ff1ff06f  jal          x0, 0x00000280  # target 0x00000280
loc_294:
    294: 0ff0000f  fence        0xf, 0xf
    298: 00008067  jalr         x0, 0(x1)
loc_29c:
    29c: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    2a0: 000aaa03  lw           x20, 0(x21)  # param e2e_context_decode_token; 0x00000780
    2a4: 007a7d13  andi         x26, x20, 7
    2a8: ff8a7a13  andi         x20, x20, -8
    2ac: 01af8ab3  add          x21, x31, x26
    2b0: 007afb93  andi         x23, x21, 7
    2b4: 003ada93  srli         x21, x21, 3
    2b8: 00ba9a93  slli         x21, x21, 11
    2bc: 014a8ab3  add          x21, x21, x20
    2c0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000002c0
    2c4: 030b0b13  addi         x22, x22, 48  # x22 = 0x000002f0
    2c8: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2cc: 890e8e93  addi         x29, x29, -1904  # x29 = 0x00011890
    2d0: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00011890
    2d4: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    2d8: 03cd8db3  mul          x27, x27, x28
    2dc: 01bb0b33  add          x22, x22, x27
    2e0: 001b9b93  slli         x23, x23, 1
    2e4: 017b0b33  add          x22, x22, x23
    2e8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    2ec: 00008067  jalr         x0, 0(x1)
    2f0: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    2f4: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    2f8: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    2fc: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    300: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    304: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    308: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    30c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    310: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    314: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    318: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    31c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_320:
    320: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    324: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    328: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    32c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    330: 015a6463  bltu         x20, x21, 0x00000338  # target 0x00000338
    334: fedff06f  jal          x0, 0x00000320  # target 0x00000320
loc_338:
    338: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    33c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    340: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    344: 014a1a13  slli         x20, x20, 20
    348: 014a5a13  srli         x20, x20, 20
    34c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_350:
    350: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    354: 000b0463  beq          x22, x0, 0x0000035c  # target 0x0000035c
    358: ff9ff06f  jal          x0, 0x00000350  # target 0x00000350
loc_35c:
    35c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    360: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    364: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    368: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    36c: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    370: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    374: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    378: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    37c: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    380: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    384: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    388: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    38c: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    390: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    394: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    398: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    39c: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    3a0: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    3a4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    3a8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    3ac: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    3b0: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_3b4:
    3b4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    3b8: 000b0463  beq          x22, x0, 0x000003c0  # target 0x000003c0
    3bc: ff9ff06f  jal          x0, 0x000003b4  # target 0x000003b4
loc_3c0:
    3c0: 00008067  jalr         x0, 0(x1)
loc_3c4:
    3c4: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    3c8: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x0000078c
    3cc: 007a7d13  andi         x26, x20, 7
    3d0: ff8a7a13  andi         x20, x20, -8
    3d4: 01af8ab3  add          x21, x31, x26
    3d8: 007afb93  andi         x23, x21, 7
    3dc: 003ada93  srli         x21, x21, 3
    3e0: 00ba9a93  slli         x21, x21, 11
    3e4: 014a8ab3  add          x21, x21, x20
    3e8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000003e8
    3ec: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000418
    3f0: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    3f4: 890e8e93  addi         x29, x29, -1904  # x29 = 0x00011890
    3f8: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00011890
    3fc: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    400: 03cd8db3  mul          x27, x27, x28
    404: 01bb0b33  add          x22, x22, x27
    408: 001b9b93  slli         x23, x23, 1
    40c: 017b0b33  add          x22, x22, x23
    410: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    414: 00008067  jalr         x0, 0(x1)
    418: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    41c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    420: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    424: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    428: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    42c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    430: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    434: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    438: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    43c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    440: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    444: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_448:
    448: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000448
    44c: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x00000540
    450: 00012cb7  lui          x25, 0x00012  # x25 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    454: 890c8c93  addi         x25, x25, -1904  # x25 = 0x00011890
    458: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x00011890
    45c: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    460: 038b8bb3  mul          x23, x23, x24
    464: 017a0a33  add          x20, x20, x23
loc_468:
    468: 001f1a93  slli         x21, x30, 1
    46c: 014a8ab3  add          x21, x21, x20
    470: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_474:
    474: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    478: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    47c: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    480: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    484: 018be463  bltu         x23, x24, 0x0000048c  # target 0x0000048c
    488: fedff06f  jal          x0, 0x00000474  # target 0x00000474
loc_48c:
    48c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    490: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    494: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    498: 014b9b93  slli         x23, x23, 20
    49c: 014bdb93  srli         x23, x23, 20
    4a0: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_4a4:
    4a4: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    4a8: 000c8463  beq          x25, x0, 0x000004b0  # target 0x000004b0
    4ac: ff9ff06f  jal          x0, 0x000004a4  # target 0x000004a4
loc_4b0:
    4b0: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    4b4: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    4b8: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    4bc: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    4c0: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    4c4: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    4c8: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    4cc: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    4d0: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    4d4: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    4d8: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    4dc: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    4e0: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4e4: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    4e8: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    4ec: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    4f0: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    4f4: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    4f8: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    4fc: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    500: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    504: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_508:
    508: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    50c: 000c8463  beq          x25, x0, 0x00000514  # target 0x00000514
    510: ff9ff06f  jal          x0, 0x00000508  # target 0x00000508
loc_514:
    514: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    518: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    51c: 016e8eb3  add          x29, x29, x22
    520: 001f0f13  addi         x30, x30, 1
    524: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    528: 015f1663  bne          x30, x21, 0x00000534  # target 0x00000534
    52c: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    530: 016f8fb3  add          x31, x31, x22
loc_534:
    534: fffe0e13  addi         x28, x28, -1
    538: f20e18e3  bne          x28, x0, 0x00000468  # target 0x00000468
    53c: 00008067  jalr         x0, 0(x1)
    540: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    544: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    548: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    54c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    550: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    554: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    558: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    55c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    560: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    564: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    568: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    56c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    570:           j FW_BRISC+4   # return to firmware, linked at install
