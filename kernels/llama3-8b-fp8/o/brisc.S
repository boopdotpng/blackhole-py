# llama3 8b-fp8 decode: o, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x780=e2e_context_decode_token, 0x784=e2e_l0_q, 0x788=input_scale_0, 0x78c=input_scale_1, 0x790=output_scale_0_0, 0x794=output_scale_0_1, 0x798=e2e_x_b, 0x79c=e2e_x_a, 0x11880=e2e_q_compact, 0x11884=e2e_l0_q_row_start, 0x11888=dense_start, 0x1188c=e2e_l0_q_rows, 0x11890=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000252b7  lui          x5, 0x00025  # x5 = 0x00025000
      c: 88028293  addi         x5, x5, -1920  # x5 = 0x00024880
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00024880
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     24: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     28: 00012537  lui          x10, 0x00012  # x10 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     2c: 08050513  addi         x10, x10, 128  # x10 = 0x00012080
     30: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00012080
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
     80: 2c4000ef  jal          x1, 0x00000344  # target 0x00000344; x1 = 0x00000084
     84: 2dc000ef  jal          x1, 0x00000360  # target 0x00000360; x1 = 0x00000088
     88: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     8c: 2f0000ef  jal          x1, 0x0000037c  # target 0x0000037c; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 00025eb7  lui          x29, 0x00025  # x29 = 0x00025000
     a4: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00024880
     a8: 358000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x000000ac
     ac: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     b0: 2cc000ef  jal          x1, 0x0000037c  # target 0x0000037c; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 00025eb7  lui          x29, 0x00025  # x29 = 0x00025000
     c8: 080e8e93  addi         x29, x29, 128  # x29 = 0x00025080
     cc: 334000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x000000d0
     d0: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     d4: 2a8000ef  jal          x1, 0x0000037c  # target 0x0000037c; x1 = 0x000000d8
     d8: 000a8213  addi         x4, x21, 0
     dc: 000b0293  addi         x5, x22, 0
     e0: 00020f93  addi         x31, x4, 0
     e4: 00028f13  addi         x30, x5, 0
     e8: 00026eb7  lui          x29, 0x00026  # x29 = 0x00026000
     ec: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00025880
     f0: 310000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x000000f4
     f4: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     f8: 284000ef  jal          x1, 0x0000037c  # target 0x0000037c; x1 = 0x000000fc
     fc: 000a8213  addi         x4, x21, 0
    100: 000b0293  addi         x5, x22, 0
    104: 00020f93  addi         x31, x4, 0
    108: 00028f13  addi         x30, x5, 0
    10c: 00026eb7  lui          x29, 0x00026  # x29 = 0x00026000
    110: 080e8e93  addi         x29, x29, 128  # x29 = 0x00026080
    114: 2ec000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x00000118
    118: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    11c: 388000ef  jal          x1, 0x000004a4  # target 0x000004a4; x1 = 0x00000120
    120: 000a8213  addi         x4, x21, 0
    124: 000b0293  addi         x5, x22, 0
    128: 00020f93  addi         x31, x4, 0
    12c: 00028f13  addi         x30, x5, 0
    130: 00027eb7  lui          x29, 0x00027  # x29 = 0x00027000
    134: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00026880
    138: 2c8000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x0000013c
    13c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    140: 364000ef  jal          x1, 0x000004a4  # target 0x000004a4; x1 = 0x00000144
    144: 000a8213  addi         x4, x21, 0
    148: 000b0293  addi         x5, x22, 0
    14c: 00020f93  addi         x31, x4, 0
    150: 00028f13  addi         x30, x5, 0
    154: 00027eb7  lui          x29, 0x00027  # x29 = 0x00027000
    158: 080e8e93  addi         x29, x29, 128  # x29 = 0x00027080
    15c: 2a4000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x00000160
    160: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    164: 340000ef  jal          x1, 0x000004a4  # target 0x000004a4; x1 = 0x00000168
    168: 000a8213  addi         x4, x21, 0
    16c: 000b0293  addi         x5, x22, 0
    170: 00020f93  addi         x31, x4, 0
    174: 00028f13  addi         x30, x5, 0
    178: 00028eb7  lui          x29, 0x00028  # x29 = 0x00028000
    17c: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00027880
    180: 280000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x00000184
    184: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    188: 31c000ef  jal          x1, 0x000004a4  # target 0x000004a4; x1 = 0x0000018c
    18c: 000a8213  addi         x4, x21, 0
    190: 000b0293  addi         x5, x22, 0
    194: 00020f93  addi         x31, x4, 0
    198: 00028f13  addi         x30, x5, 0
    19c: 00028eb7  lui          x29, 0x00028  # x29 = 0x00028000
    1a0: 080e8e93  addi         x29, x29, 128  # x29 = 0x00028080
    1a4: 25c000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x000001a8
    1a8: 1b8000ef  jal          x1, 0x00000360  # target 0x00000360; x1 = 0x000001ac
    1ac: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1b0: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1b4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    1b8: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    1bc: 00520233  add          x4, x4, x5
    1c0: 00027337  lui          x6, 0x00027  # x6 = 0x00027000
    1c4: 88030313  addi         x6, x6, -1920  # x6 = 0x00026880
    1c8: 00626663  bltu         x4, x6, 0x000001d4  # target 0x000001d4
    1cc: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    1d0: 40720233  sub          x4, x4, x7
loc_1d4:
    1d4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1d8: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1dc: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1e0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1e4: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1e8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    1ec: 00420213  addi         x4, x4, 4
    1f0: 01021213  slli         x4, x4, 16
    1f4: 01025213  srli         x4, x4, 16
    1f8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1fc: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    200: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    204: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    208: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    20c: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    210: 0ff0000f  fence        0xf, 0xf
    214: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    218: 88c28293  addi         x5, x5, -1908  # x5 = 0x0001188c
    21c: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0001188c
    220: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    224: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x00000784
    228: ff82f293  andi         x5, x5, -8
    22c: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    230: 88448493  addi         x9, x9, -1916  # x9 = 0x00011884
    234: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x00011884
    238: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    23c: 028383b3  mul          x7, x7, x8
    240: 0073f313  andi         x6, x7, 7
    244: 0033d393  srli         x7, x7, 3
    248: 00b39393  slli         x7, x7, 11
    24c: 007282b3  add          x5, x5, x7
    250: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    254: 00020413  addi         x8, x4, 0
loc_258:
    258: 0e83f463  bgeu         x7, x8, 0x00000340  # target 0x00000340
    25c: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    260: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    264: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_268:
    268: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    26c: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    270: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    274: 40a485b3  sub          x11, x9, x10
    278: 01059593  slli         x11, x11, 16
    27c: 0105d593  srli         x11, x11, 16
    280: 04000613  addi         x12, x0, 64  # x12 = 0x00000040
    284: 40b60633  sub          x12, x12, x11
    288: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    28c: 00d67663  bgeu         x12, x13, 0x00000298  # target 0x00000298
    290: 0ff0000f  fence        0xf, 0xf
    294: fd5ff06f  jal          x0, 0x00000268  # target 0x00000268
loc_298:
    298: 0ff0000f  fence        0xf, 0xf
    29c: 0a8000ef  jal          x1, 0x00000344  # target 0x00000344; x1 = 0x000002a0
    2a0: 0c0000ef  jal          x1, 0x00000360  # target 0x00000360; x1 = 0x000002a4
    2a4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2a8: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    2ac: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    2b0: 00028f93  addi         x31, x5, 0
    2b4: 00030f13  addi         x30, x6, 0
    2b8: 00048e93  addi         x29, x9, 0
    2bc: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    2c0: 268000ef  jal          x1, 0x00000528  # target 0x00000528; x1 = 0x000002c4
    2c4: 000f8293  addi         x5, x31, 0
    2c8: 000f0313  addi         x6, x30, 0
    2cc: 094000ef  jal          x1, 0x00000360  # target 0x00000360; x1 = 0x000002d0
    2d0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2d4: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2d8: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    2dc: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2e0: 00a484b3  add          x9, x9, x10
    2e4: 000225b7  lui          x11, 0x00022  # x11 = 0x00022000
    2e8: 08058593  addi         x11, x11, 128  # x11 = 0x00022080
    2ec: 00b4e663  bltu         x9, x11, 0x000002f8  # target 0x000002f8
    2f0: 00010637  lui          x12, 0x00010  # x12 = 0x00010000
    2f4: 40c484b3  sub          x9, x9, x12
loc_2f8:
    2f8: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2fc: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    300: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    304: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    308: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    30c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    310: 00448493  addi         x9, x9, 4
    314: 01049493  slli         x9, x9, 16
    318: 0104d493  srli         x9, x9, 16
    31c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    320: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    324: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    328: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    32c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    330: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    334: 0ff0000f  fence        0xf, 0xf
    338: 00138393  addi         x7, x7, 1
    33c: f1dff06f  jal          x0, 0x00000258  # target 0x00000258
loc_340:
    340: 3100006f  jal          x0, 0x00000650  # target 0x00000650
loc_344:
    344: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    348: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    34c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    350: 000a0463  beq          x20, x0, 0x00000358  # target 0x00000358
    354: ff1ff06f  jal          x0, 0x00000344  # target 0x00000344
loc_358:
    358: 0ff0000f  fence        0xf, 0xf
    35c: 00008067  jalr         x0, 0(x1)
loc_360:
    360: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    364: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    368: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    36c: 000a0463  beq          x20, x0, 0x00000374  # target 0x00000374
    370: ff1ff06f  jal          x0, 0x00000360  # target 0x00000360
loc_374:
    374: 0ff0000f  fence        0xf, 0xf
    378: 00008067  jalr         x0, 0(x1)
loc_37c:
    37c: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    380: 000aaa03  lw           x20, 0(x21)  # param e2e_context_decode_token; 0x00000780
    384: 007a7d13  andi         x26, x20, 7
    388: ff8a7a13  andi         x20, x20, -8
    38c: 01af8ab3  add          x21, x31, x26
    390: 007afb93  andi         x23, x21, 7
    394: 003ada93  srli         x21, x21, 3
    398: 00ba9a93  slli         x21, x21, 11
    39c: 014a8ab3  add          x21, x21, x20
    3a0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000003a0
    3a4: 030b0b13  addi         x22, x22, 48  # x22 = 0x000003d0
    3a8: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    3ac: 890e8e93  addi         x29, x29, -1904  # x29 = 0x00011890
    3b0: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00011890
    3b4: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    3b8: 03cd8db3  mul          x27, x27, x28
    3bc: 01bb0b33  add          x22, x22, x27
    3c0: 001b9b93  slli         x23, x23, 1
    3c4: 017b0b33  add          x22, x22, x23
    3c8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    3cc: 00008067  jalr         x0, 0(x1)
    3d0: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3d4: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3d8: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    3dc: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    3e0: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3e4: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3e8: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    3ec: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    3f0: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    3f4: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3f8: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    3fc: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_400:
    400: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    404: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    408: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    40c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    410: 015a6463  bltu         x20, x21, 0x00000418  # target 0x00000418
    414: fedff06f  jal          x0, 0x00000400  # target 0x00000400
loc_418:
    418: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    41c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    420: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    424: 014a1a13  slli         x20, x20, 20
    428: 014a5a13  srli         x20, x20, 20
    42c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_430:
    430: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    434: 000b0463  beq          x22, x0, 0x0000043c  # target 0x0000043c
    438: ff9ff06f  jal          x0, 0x00000430  # target 0x00000430
loc_43c:
    43c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    440: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    444: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    448: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    44c: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    450: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    454: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    458: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    45c: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    460: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    464: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    468: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    46c: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    470: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    474: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    478: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    47c: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    480: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    484: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    488: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    48c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    490: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_494:
    494: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    498: 000b0463  beq          x22, x0, 0x000004a0  # target 0x000004a0
    49c: ff9ff06f  jal          x0, 0x00000494  # target 0x00000494
loc_4a0:
    4a0: 00008067  jalr         x0, 0(x1)
loc_4a4:
    4a4: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    4a8: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x0000079c
    4ac: 007a7d13  andi         x26, x20, 7
    4b0: ff8a7a13  andi         x20, x20, -8
    4b4: 01af8ab3  add          x21, x31, x26
    4b8: 007afb93  andi         x23, x21, 7
    4bc: 003ada93  srli         x21, x21, 3
    4c0: 00ba9a93  slli         x21, x21, 11
    4c4: 014a8ab3  add          x21, x21, x20
    4c8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004c8
    4cc: 030b0b13  addi         x22, x22, 48  # x22 = 0x000004f8
    4d0: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    4d4: 890e8e93  addi         x29, x29, -1904  # x29 = 0x00011890
    4d8: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00011890
    4dc: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    4e0: 03cd8db3  mul          x27, x27, x28
    4e4: 01bb0b33  add          x22, x22, x27
    4e8: 001b9b93  slli         x23, x23, 1
    4ec: 017b0b33  add          x22, x22, x23
    4f0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4f4: 00008067  jalr         x0, 0(x1)
    4f8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4fc: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    500: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    504: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    508: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    50c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    510: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    514: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    518: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    51c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    520: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    524: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_528:
    528: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000528
    52c: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x00000620
    530: 00012cb7  lui          x25, 0x00012  # x25 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    534: 890c8c93  addi         x25, x25, -1904  # x25 = 0x00011890
    538: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x00011890
    53c: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    540: 038b8bb3  mul          x23, x23, x24
    544: 017a0a33  add          x20, x20, x23
loc_548:
    548: 001f1a93  slli         x21, x30, 1
    54c: 014a8ab3  add          x21, x21, x20
    550: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_554:
    554: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    558: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    55c: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    560: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    564: 018be463  bltu         x23, x24, 0x0000056c  # target 0x0000056c
    568: fedff06f  jal          x0, 0x00000554  # target 0x00000554
loc_56c:
    56c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    570: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    574: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    578: 014b9b93  slli         x23, x23, 20
    57c: 014bdb93  srli         x23, x23, 20
    580: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_584:
    584: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    588: 000c8463  beq          x25, x0, 0x00000590  # target 0x00000590
    58c: ff9ff06f  jal          x0, 0x00000584  # target 0x00000584
loc_590:
    590: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    594: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    598: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    59c: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    5a0: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    5a4: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    5a8: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    5ac: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    5b0: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    5b4: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    5b8: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    5bc: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    5c0: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5c4: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    5c8: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    5cc: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    5d0: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    5d4: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    5d8: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    5dc: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    5e0: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    5e4: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_5e8:
    5e8: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    5ec: 000c8463  beq          x25, x0, 0x000005f4  # target 0x000005f4
    5f0: ff9ff06f  jal          x0, 0x000005e8  # target 0x000005e8
loc_5f4:
    5f4: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5f8: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    5fc: 016e8eb3  add          x29, x29, x22
    600: 001f0f13  addi         x30, x30, 1
    604: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    608: 015f1663  bne          x30, x21, 0x00000614  # target 0x00000614
    60c: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    610: 016f8fb3  add          x31, x31, x22
loc_614:
    614: fffe0e13  addi         x28, x28, -1
    618: f20e18e3  bne          x28, x0, 0x00000548  # target 0x00000548
    61c: 00008067  jalr         x0, 0(x1)
    620: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    624: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    628: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    62c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    630: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    634: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    638: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    63c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    640: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    644: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    648: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    64c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    650:           j FW_BRISC+4   # return to firmware, linked at install
