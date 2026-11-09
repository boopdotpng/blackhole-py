# llama3 1b decode: lm, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x7c0=e2e_x_a_decode_token, 0x7c4=e2e_lm_weight, 0x7c8=e2e_final_norm, 0x8180=e2e_logits, 0x8184=e2e_lm_weight_row_start, 0x8188=e2e_lm_weight_rows, 0x818c=dram_port
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000952b7  lui          x5, 0x00095  # x5 = 0x00095000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00095000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     20: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     24: 00090537  lui          x10, 0x00090  # x10 = 0x00090000
     28: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00090000
     2c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     30: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
     34: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     38: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     3c: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     40: 0004a203  lw           x4, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_44:
     44: ffb4c4b7  lui          x9, 0xffb4c  # x9 = 0xffb4c000
     48: 02048493  addi         x9, x9, 32  # x9 = 0xffb4c020
     4c: 0004d283  lhu          x5, 0(x9)  # 0xffb4c020
     50: 40520333  sub          x6, x4, x5
     54: 01031313  slli         x6, x6, 16
     58: 01035313  srli         x6, x6, 16
     5c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     60: 406383b3  sub          x7, x7, x6
     64: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
     68: 0083f663  bgeu         x7, x8, 0x00000074  # target 0x00000074
     6c: 0ff0000f  fence        0xf, 0xf
     70: fd5ff06f  jal          x0, 0x00000044  # target 0x00000044
loc_74:
     74: 0ff0000f  fence        0xf, 0xf
     78: 224000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x0000007c
     7c: 23c000ef  jal          x1, 0x000002b8  # target 0x000002b8; x1 = 0x00000080
     80: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     84: 250000ef  jal          x1, 0x000002d4  # target 0x000002d4; x1 = 0x00000088
     88: 000a8213  addi         x4, x21, 0
     8c: 000b0293  addi         x5, x22, 0
     90: 00020f93  addi         x31, x4, 0
     94: 00028f13  addi         x30, x5, 0
     98: 00095eb7  lui          x29, 0x00095  # x29 = 0x00095000
     9c: 2bc000ef  jal          x1, 0x00000358  # target 0x00000358; x1 = 0x000000a0
     a0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     a4: 230000ef  jal          x1, 0x000002d4  # target 0x000002d4; x1 = 0x000000a8
     a8: 000a8213  addi         x4, x21, 0
     ac: 000b0293  addi         x5, x22, 0
     b0: 00020f93  addi         x31, x4, 0
     b4: 00028f13  addi         x30, x5, 0
     b8: 00096eb7  lui          x29, 0x00096  # x29 = 0x00096000
     bc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00095800
     c0: 298000ef  jal          x1, 0x00000358  # target 0x00000358; x1 = 0x000000c4
     c4: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     c8: 334000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x000000cc
     cc: 000a8213  addi         x4, x21, 0
     d0: 000b0293  addi         x5, x22, 0
     d4: 00020f93  addi         x31, x4, 0
     d8: 00028f13  addi         x30, x5, 0
     dc: 00096eb7  lui          x29, 0x00096  # x29 = 0x00096000
     e0: 278000ef  jal          x1, 0x00000358  # target 0x00000358; x1 = 0x000000e4
     e4: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     e8: 314000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x000000ec
     ec: 000a8213  addi         x4, x21, 0
     f0: 000b0293  addi         x5, x22, 0
     f4: 00020f93  addi         x31, x4, 0
     f8: 00028f13  addi         x30, x5, 0
     fc: 00097eb7  lui          x29, 0x00097  # x29 = 0x00097000
    100: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00096800
    104: 254000ef  jal          x1, 0x00000358  # target 0x00000358; x1 = 0x00000108
    108: 1b0000ef  jal          x1, 0x000002b8  # target 0x000002b8; x1 = 0x0000010c
    10c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    110: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    114: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    118: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    11c: 00520233  add          x4, x4, x5
    120: 00097337  lui          x6, 0x00097  # x6 = 0x00097000
    124: 00626663  bltu         x4, x6, 0x00000130  # target 0x00000130
    128: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    12c: 40720233  sub          x4, x4, x7
loc_130:
    130: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    134: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    138: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    13c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    140: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    144: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    148: 00420213  addi         x4, x4, 4
    14c: 01021213  slli         x4, x4, 16
    150: 01025213  srli         x4, x4, 16
    154: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    158: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    15c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    160: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    164: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    168: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    16c: 0ff0000f  fence        0xf, 0xf
    170: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    174: 18828293  addi         x5, x5, 392  # x5 = 0x00008188
    178: 0002a203  lw           x4, 0(x5)  # param e2e_lm_weight_rows; 0x00008188
    17c: 7c400393  addi         x7, x0, 1988  # x7 = 0x000007c4
    180: 0003a283  lw           x5, 0(x7)  # param e2e_lm_weight; 0x000007c4
    184: ff82f293  andi         x5, x5, -8
    188: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    18c: 18448493  addi         x9, x9, 388  # x9 = 0x00008184
    190: 0004a383  lw           x7, 0(x9)  # param e2e_lm_weight_row_start; 0x00008184
    194: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    198: 028383b3  mul          x7, x7, x8
    19c: 0073f313  andi         x6, x7, 7
    1a0: 0033d393  srli         x7, x7, 3
    1a4: 00b39393  slli         x7, x7, 11
    1a8: 007282b3  add          x5, x5, x7
    1ac: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1b0: 00020413  addi         x8, x4, 0
loc_1b4:
    1b4: 0e83f263  bgeu         x7, x8, 0x00000298  # target 0x00000298
    1b8: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    1bc: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    1c0: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_1c4:
    1c4: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1c8: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    1cc: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    1d0: 40a485b3  sub          x11, x9, x10
    1d4: 01059593  slli         x11, x11, 16
    1d8: 0105d593  srli         x11, x11, 16
    1dc: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    1e0: 40b60633  sub          x12, x12, x11
    1e4: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    1e8: 00d67663  bgeu         x12, x13, 0x000001f4  # target 0x000001f4
    1ec: 0ff0000f  fence        0xf, 0xf
    1f0: fd5ff06f  jal          x0, 0x000001c4  # target 0x000001c4
loc_1f4:
    1f4: 0ff0000f  fence        0xf, 0xf
    1f8: 0a4000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x000001fc
    1fc: 0bc000ef  jal          x1, 0x000002b8  # target 0x000002b8; x1 = 0x00000200
    200: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    204: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    208: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    20c: 00028f93  addi         x31, x5, 0
    210: 00030f13  addi         x30, x6, 0
    214: 00048e93  addi         x29, x9, 0
    218: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    21c: 264000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000220
    220: 000f8293  addi         x5, x31, 0
    224: 000f0313  addi         x6, x30, 0
    228: 090000ef  jal          x1, 0x000002b8  # target 0x000002b8; x1 = 0x0000022c
    22c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    230: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    234: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    238: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    23c: 00a484b3  add          x9, x9, x10
    240: 000925b7  lui          x11, 0x00092  # x11 = 0x00092000
    244: 00b4e663  bltu         x9, x11, 0x00000250  # target 0x00000250
    248: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    24c: 40c484b3  sub          x9, x9, x12
loc_250:
    250: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    254: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    258: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    25c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    260: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    264: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    268: 00248493  addi         x9, x9, 2
    26c: 01049493  slli         x9, x9, 16
    270: 0104d493  srli         x9, x9, 16
    274: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    278: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    27c: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    280: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    284: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    288: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    28c: 0ff0000f  fence        0xf, 0xf
    290: 00138393  addi         x7, x7, 1
    294: f21ff06f  jal          x0, 0x000001b4  # target 0x000001b4
loc_298:
    298: 3100006f  jal          x0, 0x000005a8  # target 0x000005a8
loc_29c:
    29c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    2a0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    2a4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    2a8: 000a0463  beq          x20, x0, 0x000002b0  # target 0x000002b0
    2ac: ff1ff06f  jal          x0, 0x0000029c  # target 0x0000029c
loc_2b0:
    2b0: 0ff0000f  fence        0xf, 0xf
    2b4: 00008067  jalr         x0, 0(x1)
loc_2b8:
    2b8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    2bc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    2c0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    2c4: 000a0463  beq          x20, x0, 0x000002cc  # target 0x000002cc
    2c8: ff1ff06f  jal          x0, 0x000002b8  # target 0x000002b8
loc_2cc:
    2cc: 0ff0000f  fence        0xf, 0xf
    2d0: 00008067  jalr         x0, 0(x1)
loc_2d4:
    2d4: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    2d8: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x000007c0
    2dc: 007a7d13  andi         x26, x20, 7
    2e0: ff8a7a13  andi         x20, x20, -8
    2e4: 01af8ab3  add          x21, x31, x26
    2e8: 007afb93  andi         x23, x21, 7
    2ec: 003ada93  srli         x21, x21, 3
    2f0: 00ba9a93  slli         x21, x21, 11
    2f4: 014a8ab3  add          x21, x21, x20
    2f8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000002f8
    2fc: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000328
    300: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    304: 18ce8e93  addi         x29, x29, 396  # x29 = 0x0000818c
    308: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000818c
    30c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    310: 03cd8db3  mul          x27, x27, x28
    314: 01bb0b33  add          x22, x22, x27
    318: 001b9b93  slli         x23, x23, 1
    31c: 017b0b33  add          x22, x22, x23
    320: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    324: 00008067  jalr         x0, 0(x1)
    328: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    32c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    330: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    334: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    338: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    33c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    340: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    344: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    348: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    34c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    350: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    354: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_358:
    358: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    35c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    360: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    364: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    368: 015a6463  bltu         x20, x21, 0x00000370  # target 0x00000370
    36c: fedff06f  jal          x0, 0x00000358  # target 0x00000358
loc_370:
    370: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    374: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    378: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    37c: 014a1a13  slli         x20, x20, 20
    380: 014a5a13  srli         x20, x20, 20
    384: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_388:
    388: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    38c: 000b0463  beq          x22, x0, 0x00000394  # target 0x00000394
    390: ff9ff06f  jal          x0, 0x00000388  # target 0x00000388
loc_394:
    394: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    398: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    39c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    3a0: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    3a4: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    3a8: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    3ac: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    3b0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    3b4: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    3b8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    3bc: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    3c0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    3c4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3c8: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    3cc: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    3d0: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    3d4: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    3d8: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    3dc: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    3e0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    3e4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    3e8: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_3ec:
    3ec: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    3f0: 000b0463  beq          x22, x0, 0x000003f8  # target 0x000003f8
    3f4: ff9ff06f  jal          x0, 0x000003ec  # target 0x000003ec
loc_3f8:
    3f8: 00008067  jalr         x0, 0(x1)
loc_3fc:
    3fc: 7c800a93  addi         x21, x0, 1992  # x21 = 0x000007c8
    400: 000aaa03  lw           x20, 0(x21)  # param e2e_final_norm; 0x000007c8
    404: 007a7d13  andi         x26, x20, 7
    408: ff8a7a13  andi         x20, x20, -8
    40c: 01af8ab3  add          x21, x31, x26
    410: 007afb93  andi         x23, x21, 7
    414: 003ada93  srli         x21, x21, 3
    418: 00ba9a93  slli         x21, x21, 11
    41c: 014a8ab3  add          x21, x21, x20
    420: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000420
    424: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000450
    428: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    42c: 18ce8e93  addi         x29, x29, 396  # x29 = 0x0000818c
    430: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000818c
    434: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    438: 03cd8db3  mul          x27, x27, x28
    43c: 01bb0b33  add          x22, x22, x27
    440: 001b9b93  slli         x23, x23, 1
    444: 017b0b33  add          x22, x22, x23
    448: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    44c: 00008067  jalr         x0, 0(x1)
    450: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    454: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    458: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    45c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    460: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    464: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    468: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    46c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    470: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    474: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    478: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    47c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_480:
    480: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000480
    484: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x00000578
    488: 00008cb7  lui          x25, 0x00008  # x25 = 0x00008000
    48c: 18cc8c93  addi         x25, x25, 396  # x25 = 0x0000818c
    490: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0000818c
    494: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    498: 038b8bb3  mul          x23, x23, x24
    49c: 017a0a33  add          x20, x20, x23
loc_4a0:
    4a0: 001f1a93  slli         x21, x30, 1
    4a4: 014a8ab3  add          x21, x21, x20
    4a8: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_4ac:
    4ac: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    4b0: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    4b4: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    4b8: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    4bc: 018be463  bltu         x23, x24, 0x000004c4  # target 0x000004c4
    4c0: fedff06f  jal          x0, 0x000004ac  # target 0x000004ac
loc_4c4:
    4c4: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    4c8: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    4cc: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    4d0: 014b9b93  slli         x23, x23, 20
    4d4: 014bdb93  srli         x23, x23, 20
    4d8: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_4dc:
    4dc: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    4e0: 000c8463  beq          x25, x0, 0x000004e8  # target 0x000004e8
    4e4: ff9ff06f  jal          x0, 0x000004dc  # target 0x000004dc
loc_4e8:
    4e8: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    4ec: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    4f0: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    4f4: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    4f8: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    4fc: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    500: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    504: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    508: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    50c: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    510: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    514: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    518: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    51c: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    520: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    524: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    528: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    52c: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    530: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    534: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    538: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    53c: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_540:
    540: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    544: 000c8463  beq          x25, x0, 0x0000054c  # target 0x0000054c
    548: ff9ff06f  jal          x0, 0x00000540  # target 0x00000540
loc_54c:
    54c: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    550: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    554: 016e8eb3  add          x29, x29, x22
    558: 001f0f13  addi         x30, x30, 1
    55c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    560: 015f1663  bne          x30, x21, 0x0000056c  # target 0x0000056c
    564: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    568: 016f8fb3  add          x31, x31, x22
loc_56c:
    56c: fffe0e13  addi         x28, x28, -1
    570: f20e18e3  bne          x28, x0, 0x000004a0  # target 0x000004a0
    574: 00008067  jalr         x0, 0(x1)
    578: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    57c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    580: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    584: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    588: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    58c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    590: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    594: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    598: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    59c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5a0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    5a4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    5a8:           j FW_BRISC+4   # return to firmware, linked at install
