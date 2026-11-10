# llama3 1b decode: lm, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_lm_weight, 0x788=e2e_final_norm, 0xe9c0=e2e_logits, 0xe9c4=e2e_lm_weight_row_start, 0xe9c8=e2e_lm_weight_rows, 0xe9cc=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000142b7  lui          x5, 0x00014  # x5 = 0x00014000
      c: fc028293  addi         x5, x5, -64  # x5 = 0x00013fc0
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00013fc0
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     24: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     28: 0000f537  lui          x10, 0x0000f  # x10 = 0x0000f000
     2c: fc050513  addi         x10, x10, -64  # x10 = 0x0000efc0
     30: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x0000efc0
     34: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     38: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
     3c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     40: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     44: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     48: 0004a203  lw           x4, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_4c:
     4c: ffb4c4b7  lui          x9, 0xffb4c  # x9 = 0xffb4c000
     50: 02048493  addi         x9, x9, 32  # x9 = 0xffb4c020
     54: 0004d283  lhu          x5, 0(x9)  # 0xffb4c020
     58: 40520333  sub          x6, x4, x5
     5c: 01031313  slli         x6, x6, 16
     60: 01035313  srli         x6, x6, 16
     64: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     68: 406383b3  sub          x7, x7, x6
     6c: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
     70: 0083f663  bgeu         x7, x8, 0x0000007c  # target 0x0000007c
     74: 0ff0000f  fence        0xf, 0xf
     78: fd5ff06f  jal          x0, 0x0000004c  # target 0x0000004c
loc_7c:
     7c: 0ff0000f  fence        0xf, 0xf
     80: 234000ef  jal          x1, 0x000002b4  # target 0x000002b4; x1 = 0x00000084
     84: 24c000ef  jal          x1, 0x000002d0  # target 0x000002d0; x1 = 0x00000088
     88: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     8c: 260000ef  jal          x1, 0x000002ec  # target 0x000002ec; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 00014eb7  lui          x29, 0x00014  # x29 = 0x00014000
     a4: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00013fc0
     a8: 2c8000ef  jal          x1, 0x00000370  # target 0x00000370; x1 = 0x000000ac
     ac: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     b0: 23c000ef  jal          x1, 0x000002ec  # target 0x000002ec; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 00014eb7  lui          x29, 0x00014  # x29 = 0x00014000
     c8: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000147c0
     cc: 2a4000ef  jal          x1, 0x00000370  # target 0x00000370; x1 = 0x000000d0
     d0: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     d4: 340000ef  jal          x1, 0x00000414  # target 0x00000414; x1 = 0x000000d8
     d8: 000a8213  addi         x4, x21, 0
     dc: 000b0293  addi         x5, x22, 0
     e0: 00020f93  addi         x31, x4, 0
     e4: 00028f13  addi         x30, x5, 0
     e8: 00015eb7  lui          x29, 0x00015  # x29 = 0x00015000
     ec: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00014fc0
     f0: 280000ef  jal          x1, 0x00000370  # target 0x00000370; x1 = 0x000000f4
     f4: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     f8: 31c000ef  jal          x1, 0x00000414  # target 0x00000414; x1 = 0x000000fc
     fc: 000a8213  addi         x4, x21, 0
    100: 000b0293  addi         x5, x22, 0
    104: 00020f93  addi         x31, x4, 0
    108: 00028f13  addi         x30, x5, 0
    10c: 00015eb7  lui          x29, 0x00015  # x29 = 0x00015000
    110: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000157c0
    114: 25c000ef  jal          x1, 0x00000370  # target 0x00000370; x1 = 0x00000118
    118: 1b8000ef  jal          x1, 0x000002d0  # target 0x000002d0; x1 = 0x0000011c
    11c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    120: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    124: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    128: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    12c: 00520233  add          x4, x4, x5
    130: 00016337  lui          x6, 0x00016  # x6 = 0x00016000
    134: fc030313  addi         x6, x6, -64  # x6 = 0x00015fc0
    138: 00626663  bltu         x4, x6, 0x00000144  # target 0x00000144
    13c: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    140: 40720233  sub          x4, x4, x7
loc_144:
    144: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    148: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    14c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    150: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    154: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    158: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    15c: 00420213  addi         x4, x4, 4
    160: 01021213  slli         x4, x4, 16
    164: 01025213  srli         x4, x4, 16
    168: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    16c: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    170: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    174: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    178: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    17c: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    180: 0ff0000f  fence        0xf, 0xf
    184: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    188: 9c828293  addi         x5, x5, -1592  # x5 = 0x0000e9c8
    18c: 0002a203  lw           x4, 0(x5)  # param e2e_lm_weight_rows; 0x0000e9c8
    190: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    194: 0003a283  lw           x5, 0(x7)  # param e2e_lm_weight; 0x00000784
    198: ff82f293  andi         x5, x5, -8
    19c: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    1a0: 9c448493  addi         x9, x9, -1596  # x9 = 0x0000e9c4
    1a4: 0004a383  lw           x7, 0(x9)  # param e2e_lm_weight_row_start; 0x0000e9c4
    1a8: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    1ac: 028383b3  mul          x7, x7, x8
    1b0: 0073f313  andi         x6, x7, 7
    1b4: 0033d393  srli         x7, x7, 3
    1b8: 00b39393  slli         x7, x7, 11
    1bc: 007282b3  add          x5, x5, x7
    1c0: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1c4: 00020413  addi         x8, x4, 0
loc_1c8:
    1c8: 0e83f463  bgeu         x7, x8, 0x000002b0  # target 0x000002b0
    1cc: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    1d0: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    1d4: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_1d8:
    1d8: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1dc: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    1e0: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    1e4: 40a485b3  sub          x11, x9, x10
    1e8: 01059593  slli         x11, x11, 16
    1ec: 0105d593  srli         x11, x11, 16
    1f0: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    1f4: 40b60633  sub          x12, x12, x11
    1f8: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    1fc: 00d67663  bgeu         x12, x13, 0x00000208  # target 0x00000208
    200: 0ff0000f  fence        0xf, 0xf
    204: fd5ff06f  jal          x0, 0x000001d8  # target 0x000001d8
loc_208:
    208: 0ff0000f  fence        0xf, 0xf
    20c: 0a8000ef  jal          x1, 0x000002b4  # target 0x000002b4; x1 = 0x00000210
    210: 0c0000ef  jal          x1, 0x000002d0  # target 0x000002d0; x1 = 0x00000214
    214: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    218: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    21c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    220: 00028f93  addi         x31, x5, 0
    224: 00030f13  addi         x30, x6, 0
    228: 00048e93  addi         x29, x9, 0
    22c: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    230: 268000ef  jal          x1, 0x00000498  # target 0x00000498; x1 = 0x00000234
    234: 000f8293  addi         x5, x31, 0
    238: 000f0313  addi         x6, x30, 0
    23c: 094000ef  jal          x1, 0x000002d0  # target 0x000002d0; x1 = 0x00000240
    240: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    244: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    248: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    24c: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    250: 00a484b3  add          x9, x9, x10
    254: 000115b7  lui          x11, 0x00011  # x11 = 0x00011000
    258: fc058593  addi         x11, x11, -64  # x11 = 0x00010fc0
    25c: 00b4e663  bltu         x9, x11, 0x00000268  # target 0x00000268
    260: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    264: 40c484b3  sub          x9, x9, x12
loc_268:
    268: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    26c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    270: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    274: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    278: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    27c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    280: 00248493  addi         x9, x9, 2
    284: 01049493  slli         x9, x9, 16
    288: 0104d493  srli         x9, x9, 16
    28c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    290: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    294: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    298: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    29c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    2a0: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    2a4: 0ff0000f  fence        0xf, 0xf
    2a8: 00138393  addi         x7, x7, 1
    2ac: f1dff06f  jal          x0, 0x000001c8  # target 0x000001c8
loc_2b0:
    2b0: 3100006f  jal          x0, 0x000005c0  # target 0x000005c0
loc_2b4:
    2b4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    2b8: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    2bc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    2c0: 000a0463  beq          x20, x0, 0x000002c8  # target 0x000002c8
    2c4: ff1ff06f  jal          x0, 0x000002b4  # target 0x000002b4
loc_2c8:
    2c8: 0ff0000f  fence        0xf, 0xf
    2cc: 00008067  jalr         x0, 0(x1)
loc_2d0:
    2d0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    2d4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    2d8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    2dc: 000a0463  beq          x20, x0, 0x000002e4  # target 0x000002e4
    2e0: ff1ff06f  jal          x0, 0x000002d0  # target 0x000002d0
loc_2e4:
    2e4: 0ff0000f  fence        0xf, 0xf
    2e8: 00008067  jalr         x0, 0(x1)
loc_2ec:
    2ec: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    2f0: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x00000780
    2f4: 007a7d13  andi         x26, x20, 7
    2f8: ff8a7a13  andi         x20, x20, -8
    2fc: 01af8ab3  add          x21, x31, x26
    300: 007afb93  andi         x23, x21, 7
    304: 003ada93  srli         x21, x21, 3
    308: 00ba9a93  slli         x21, x21, 11
    30c: 014a8ab3  add          x21, x21, x20
    310: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000310
    314: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000340
    318: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    31c: 9cce8e93  addi         x29, x29, -1588  # x29 = 0x0000e9cc
    320: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e9cc
    324: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    328: 03cd8db3  mul          x27, x27, x28
    32c: 01bb0b33  add          x22, x22, x27
    330: 001b9b93  slli         x23, x23, 1
    334: 017b0b33  add          x22, x22, x23
    338: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    33c: 00008067  jalr         x0, 0(x1)
    340: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    344: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    348: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    34c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    350: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    354: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    358: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    35c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    360: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    364: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    368: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    36c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_370:
    370: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    374: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    378: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    37c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    380: 015a6463  bltu         x20, x21, 0x00000388  # target 0x00000388
    384: fedff06f  jal          x0, 0x00000370  # target 0x00000370
loc_388:
    388: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    38c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    390: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    394: 014a1a13  slli         x20, x20, 20
    398: 014a5a13  srli         x20, x20, 20
    39c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_3a0:
    3a0: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    3a4: 000b0463  beq          x22, x0, 0x000003ac  # target 0x000003ac
    3a8: ff9ff06f  jal          x0, 0x000003a0  # target 0x000003a0
loc_3ac:
    3ac: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    3b0: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    3b4: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    3b8: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    3bc: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    3c0: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    3c4: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    3c8: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    3cc: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    3d0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    3d4: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    3d8: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    3dc: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3e0: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    3e4: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    3e8: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    3ec: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    3f0: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    3f4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    3f8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    3fc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    400: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_404:
    404: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    408: 000b0463  beq          x22, x0, 0x00000410  # target 0x00000410
    40c: ff9ff06f  jal          x0, 0x00000404  # target 0x00000404
loc_410:
    410: 00008067  jalr         x0, 0(x1)
loc_414:
    414: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    418: 000aaa03  lw           x20, 0(x21)  # param e2e_final_norm; 0x00000788
    41c: 007a7d13  andi         x26, x20, 7
    420: ff8a7a13  andi         x20, x20, -8
    424: 01af8ab3  add          x21, x31, x26
    428: 007afb93  andi         x23, x21, 7
    42c: 003ada93  srli         x21, x21, 3
    430: 00ba9a93  slli         x21, x21, 11
    434: 014a8ab3  add          x21, x21, x20
    438: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000438
    43c: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000468
    440: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    444: 9cce8e93  addi         x29, x29, -1588  # x29 = 0x0000e9cc
    448: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e9cc
    44c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    450: 03cd8db3  mul          x27, x27, x28
    454: 01bb0b33  add          x22, x22, x27
    458: 001b9b93  slli         x23, x23, 1
    45c: 017b0b33  add          x22, x22, x23
    460: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    464: 00008067  jalr         x0, 0(x1)
    468: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    46c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    470: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    474: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    478: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    47c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    480: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    484: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    488: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    48c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    490: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    494: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_498:
    498: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000498
    49c: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x00000590
    4a0: 0000fcb7  lui          x25, 0x0000f  # x25 = 0x0000f000
    4a4: 9ccc8c93  addi         x25, x25, -1588  # x25 = 0x0000e9cc
    4a8: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0000e9cc
    4ac: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    4b0: 038b8bb3  mul          x23, x23, x24
    4b4: 017a0a33  add          x20, x20, x23
loc_4b8:
    4b8: 001f1a93  slli         x21, x30, 1
    4bc: 014a8ab3  add          x21, x21, x20
    4c0: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_4c4:
    4c4: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    4c8: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    4cc: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    4d0: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    4d4: 018be463  bltu         x23, x24, 0x000004dc  # target 0x000004dc
    4d8: fedff06f  jal          x0, 0x000004c4  # target 0x000004c4
loc_4dc:
    4dc: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    4e0: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    4e4: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    4e8: 014b9b93  slli         x23, x23, 20
    4ec: 014bdb93  srli         x23, x23, 20
    4f0: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_4f4:
    4f4: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    4f8: 000c8463  beq          x25, x0, 0x00000500  # target 0x00000500
    4fc: ff9ff06f  jal          x0, 0x000004f4  # target 0x000004f4
loc_500:
    500: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    504: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    508: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    50c: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    510: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    514: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    518: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    51c: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    520: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    524: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    528: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    52c: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    530: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    534: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    538: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    53c: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    540: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    544: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    548: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    54c: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    550: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    554: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_558:
    558: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    55c: 000c8463  beq          x25, x0, 0x00000564  # target 0x00000564
    560: ff9ff06f  jal          x0, 0x00000558  # target 0x00000558
loc_564:
    564: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    568: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    56c: 016e8eb3  add          x29, x29, x22
    570: 001f0f13  addi         x30, x30, 1
    574: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    578: 015f1663  bne          x30, x21, 0x00000584  # target 0x00000584
    57c: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    580: 016f8fb3  add          x31, x31, x22
loc_584:
    584: fffe0e13  addi         x28, x28, -1
    588: f20e18e3  bne          x28, x0, 0x000004b8  # target 0x000004b8
    58c: 00008067  jalr         x0, 0(x1)
    590: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    594: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    598: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    59c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    5a0: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5a4: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5a8: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    5ac: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    5b0: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    5b4: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5b8: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    5bc: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    5c0:           j FW_BRISC+4   # return to firmware, linked at install
