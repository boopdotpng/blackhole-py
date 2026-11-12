# llama3 1b decode: argmax, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9
# params: 0x780=e2e_token_history, 0x784=argmax_host_address, 0x788=write_pos, 0x78c=write_token, 0xea00=e2e_logits, 0xea04=argmax_start, 0xea08=argmax_count, 0xea0c=argmax_core
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0000f000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     20: 88038393  addi         x7, x7, -1920  # x7 = 0xffb00880 · riscv_local_mem + 0x880
     24: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
     28: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00010000
     2c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     30: 88438393  addi         x7, x7, -1916  # x7 = 0xffb00884 · riscv_local_mem + 0x884
     34: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     38: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     3c: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     40: 0004a203  lw           x4, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_44:
     44: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
     48: 02048493  addi         x9, x9, 32  # x9 = 0xffb48020
     4c: 0004d283  lhu          x5, 0(x9)  # 0xffb48020
     50: 40520333  sub          x6, x4, x5
     54: 01031313  slli         x6, x6, 16
     58: 01035313  srli         x6, x6, 16
     5c: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
     60: 406383b3  sub          x7, x7, x6
     64: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
     68: 0083f663  bgeu         x7, x8, 0x00000074  # target 0x00000074
     6c: 0ff0000f  fence        0xf, 0xf
     70: fd5ff06f  jal          x0, 0x00000044  # target 0x00000044
loc_74:
     74: 0ff0000f  fence        0xf, 0xf
     78: 6f8000ef  jal          x1, 0x00000770  # target 0x00000770; x1 = 0x0000007c
     7c: 710000ef  jal          x1, 0x0000078c  # target 0x0000078c; x1 = 0x00000080
     80: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     84: 724000ef  jal          x1, 0x000007a8  # target 0x000007a8; x1 = 0x00000088
     88: 000a8213  addi         x4, x21, 0
     8c: 000b0293  addi         x5, x22, 0
     90: 00020f93  addi         x31, x4, 0
     94: 00028f13  addi         x30, x5, 0
     98: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
     9c: 75c000ef  jal          x1, 0x000007f8  # target 0x000007f8; x1 = 0x000000a0
     a0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     a4: 704000ef  jal          x1, 0x000007a8  # target 0x000007a8; x1 = 0x000000a8
     a8: 000a8213  addi         x4, x21, 0
     ac: 000b0293  addi         x5, x22, 0
     b0: 00020f93  addi         x31, x4, 0
     b4: 00028f13  addi         x30, x5, 0
     b8: 00010eb7  lui          x29, 0x00010  # x29 = 0x00010000
     bc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0000f800
     c0: 738000ef  jal          x1, 0x000007f8  # target 0x000007f8; x1 = 0x000000c4
     c4: 6c8000ef  jal          x1, 0x0000078c  # target 0x0000078c; x1 = 0x000000c8
     c8: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
     cc: a0838393  addi         x7, x7, -1528  # x7 = 0x0000ea08
     d0: 0003a203  lw           x4, 0(x7)  # param argmax_count; 0x0000ea08
     d4: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
     d8: a0438393  addi         x7, x7, -1532  # x7 = 0x0000ea04
     dc: 0003a283  lw           x5, 0(x7)  # param argmax_start; 0x0000ea04
     e0: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
     e4: a0c38393  addi         x7, x7, -1524  # x7 = 0x0000ea0c
     e8: 0003a303  lw           x6, 0(x7)  # param argmax_core; 0x0000ea0c
     ec: 5b100393  addi         x7, x0, 1457  # x7 = 0x000005b1
     f0: 06721463  bne          x4, x7, 0x00000158  # target 0x00000158
     f4: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
     f8: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
     fc: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
    100: 9c040413  addi         x8, x8, -1600  # x8 = 0x0000f9c0
    104: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    108: 01000593  addi         x11, x0, 16  # x11 = 0x00000010
loc_10c:
    10c: 00b57a63  bgeu         x10, x11, 0x00000120  # target 0x00000120
    110: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    114: 00440413  addi         x8, x8, 4
    118: 00150513  addi         x10, x10, 1
    11c: ff1ff06f  jal          x0, 0x0000010c  # target 0x0000010c
loc_120:
    120: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
    124: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
    128: 00010537  lui          x10, 0x00010  # x10 = 0x00010000
    12c: ba250513  addi         x10, x10, -1118  # x10 = 0x0000fba2
    130: 00951023  sh           x9, 0(x10)  # 0x0000fba2; write 0x0000ff80
    134: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
    138: ba440413  addi         x8, x8, -1116  # x8 = 0x0000fba4
    13c: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    140: 11700593  addi         x11, x0, 279  # x11 = 0x00000117
loc_144:
    144: 00b57a63  bgeu         x10, x11, 0x00000158  # target 0x00000158
    148: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    14c: 00440413  addi         x8, x8, 4
    150: 00150513  addi         x10, x10, 1
    154: ff1ff06f  jal          x0, 0x00000144  # target 0x00000144
loc_158:
    158: 5b200393  addi         x7, x0, 1458  # x7 = 0x000005b2
    15c: 04721e63  bne          x4, x7, 0x000001b8  # target 0x000001b8
    160: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
    164: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
    168: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
    16c: 9c040413  addi         x8, x8, -1600  # x8 = 0x0000f9c0
    170: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    174: 01000593  addi         x11, x0, 16  # x11 = 0x00000010
loc_178:
    178: 00b57a63  bgeu         x10, x11, 0x0000018c  # target 0x0000018c
    17c: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    180: 00440413  addi         x8, x8, 4
    184: 00150513  addi         x10, x10, 1
    188: ff1ff06f  jal          x0, 0x00000178  # target 0x00000178
loc_18c:
    18c: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
    190: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
    194: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
    198: ba440413  addi         x8, x8, -1116  # x8 = 0x0000fba4
    19c: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    1a0: 11700593  addi         x11, x0, 279  # x11 = 0x00000117
loc_1a4:
    1a4: 00b57a63  bgeu         x10, x11, 0x000001b8  # target 0x000001b8
    1a8: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    1ac: 00440413  addi         x8, x8, 4
    1b0: 00150513  addi         x10, x10, 1
    1b4: ff1ff06f  jal          x0, 0x000001a4  # target 0x000001a4
loc_1b8:
    1b8: 0ff0000f  fence        0xf, 0xf
    1bc: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1c0: 87858593  addi         x11, x11, -1928  # x11 = 0xffb00878 · riscv_local_mem + 0x878
    1c4: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x878 · 0xffb00878
    1c8: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1cc: 008383b3  add          x7, x7, x8
    1d0: 000104b7  lui          x9, 0x00010  # x9 = 0x00010000
    1d4: 0093e663  bltu         x7, x9, 0x000001e0  # target 0x000001e0
    1d8: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1dc: 40a383b3  sub          x7, x7, x10
loc_1e0:
    1e0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1e4: 87858593  addi         x11, x11, -1928  # x11 = 0xffb00878 · riscv_local_mem + 0x878
    1e8: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1ec: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1f0: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    1f4: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    1f8: 00238393  addi         x7, x7, 2
    1fc: 01039393  slli         x7, x7, 16
    200: 0103d393  srli         x7, x7, 16
    204: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    208: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    20c: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    210: ffb48437  lui          x8, 0xffb48  # x8 = 0xffb48000
    214: 02840413  addi         x8, x8, 40  # x8 = 0xffb48028
    218: 00742023  sw           x7, 0(x8)  # 0xffb48028; write runtime value
    21c: 0ff0000f  fence        0xf, 0xf
    220: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    224: 88458593  addi         x11, x11, -1916  # x11 = 0xffb00884 · riscv_local_mem + 0x884
    228: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x884 · 0xffb00884
    22c: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_230:
    230: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
    234: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
    238: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
    23c: 407404b3  sub          x9, x8, x7
    240: 01049493  slli         x9, x9, 16
    244: 0104d493  srli         x9, x9, 16
    248: 00a4f663  bgeu         x9, x10, 0x00000254  # target 0x00000254
    24c: 0ff0000f  fence        0xf, 0xf
    250: fe1ff06f  jal          x0, 0x00000230  # target 0x00000230
loc_254:
    254: 0ff0000f  fence        0xf, 0xf
    258: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    25c: 80000437  lui          x8, 0x80000  # x8 = 0x80000000 · arc_apb + 0x0
    260: fff40413  addi         x8, x8, -1  # x8 = 0x7fffffff
    264: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    268: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    26c: 0006a583  lw           x11, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    270: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    274: 02000713  addi         x14, x0, 32  # x14 = 0x00000020
loc_278:
    278: 06e6f263  bgeu         x13, x14, 0x000002dc  # target 0x000002dc
    27c: 0005a483  lw           x9, 0(x11)  # Address depends on runtime register values
    280: 00f4d493  srli         x9, x9, 15
    284: 0045a603  lw           x12, 4(x11)  # Address depends on runtime register values
    288: c0067513  andi         x10, x12, -1024
    28c: 20067793  andi         x15, x12, 512
    290: 00f56533  or           x10, x10, x15
    294: 10067793  andi         x15, x12, 256
    298: 0047d793  srli         x15, x15, 4
    29c: 00f56533  or           x10, x10, x15
    2a0: 0f067793  andi         x15, x12, 240
    2a4: 00179793  slli         x15, x15, 1
    2a8: 00f56533  or           x10, x10, x15
    2ac: 00f67793  andi         x15, x12, 15
    2b0: 00f56533  or           x10, x10, x15
    2b4: 00858593  addi         x11, x11, 8
    2b8: 00457e63  bgeu         x10, x4, 0x000002d4  # target 0x000002d4
    2bc: 00a28533  add          x10, x5, x10
    2c0: 0093e663  bltu         x7, x9, 0x000002cc  # target 0x000002cc
    2c4: 00939863  bne          x7, x9, 0x000002d4  # target 0x000002d4
    2c8: 00857663  bgeu         x10, x8, 0x000002d4  # target 0x000002d4
loc_2cc:
    2cc: 00048393  addi         x7, x9, 0
    2d0: 00050413  addi         x8, x10, 0
loc_2d4:
    2d4: 00168693  addi         x13, x13, 1
    2d8: fa1ff06f  jal          x0, 0x00000278  # target 0x00000278
loc_2dc:
    2dc: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    2e0: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    2e4: 00072683  lw           x13, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
    2e8: 00168693  addi         x13, x13, 1
    2ec: 01069693  slli         x13, x13, 16
    2f0: 0106d693  srli         x13, x13, 16
    2f4: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    2f8: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    2fc: 00d72023  sw           x13, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    300: ffb49737  lui          x14, 0xffb49  # x14 = 0xffb49000
    304: 02070713  addi         x14, x14, 32  # x14 = 0xffb49020
    308: 00d72023  sw           x13, 0(x14)  # 0xffb49020; write runtime value
    30c: 0ff0000f  fence        0xf, 0xf
    310: ffb018b7  lui          x17, 0xffb01  # x17 = 0xffb01000
    314: 88088893  addi         x17, x17, -1920  # x17 = 0xffb00880 · riscv_local_mem + 0x880
    318: 0008a683  lw           x13, 0(x17)  # riscv_local_mem + 0x880 · 0xffb00880
    31c: 00001737  lui          x14, 0x00001  # x14 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    320: 00e686b3  add          x13, x13, x14
    324: 000117b7  lui          x15, 0x00011  # x15 = 0x00011000
    328: 00f6e663  bltu         x13, x15, 0x00000334  # target 0x00000334
    32c: 00001837  lui          x16, 0x00001  # x16 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    330: 410686b3  sub          x13, x13, x16
loc_334:
    334: ffb018b7  lui          x17, 0xffb01  # x17 = 0xffb01000
    338: 88088893  addi         x17, x17, -1920  # x17 = 0xffb00880 · riscv_local_mem + 0x880
    33c: 00d8a023  sw           x13, 0(x17)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    340: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    344: 0076a023  sw           x7, 0(x13)  # TensixL1.KERNEL_CACHE_BASE · 0x00012000; write runtime value
    348: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    34c: 00468693  addi         x13, x13, 4  # x13 = 0x00012004
    350: 0086a023  sw           x8, 0(x13)  # 0x00012004; write runtime value
    354: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    358: 00868693  addi         x13, x13, 8  # x13 = 0x00012008
    35c: 00100713  addi         x14, x0, 1  # x14 = 0x00000001
    360: 00e6a023  sw           x14, 0(x13)  # 0x00012008; write 0x00000001
    364: 01000713  addi         x14, x0, 16  # x14 = 0x00000010
    368: 02e306b3  mul          x13, x6, x14
    36c: 0000f7b7  lui          x15, 0x0000f  # x15 = 0x0000f000
    370: a8078793  addi         x15, x15, -1408  # x15 = 0x0000ea80
    374: 00f686b3  add          x13, x13, x15
    378: 3f8000ef  jal          x1, 0x00000770  # target 0x00000770; x1 = 0x0000037c
    37c: 410000ef  jal          x1, 0x0000078c  # target 0x0000078c; x1 = 0x00000380
    380: 00012fb7  lui          x31, 0x00012  # x31 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    384: 00068f13  addi         x30, x13, 0
    388: 08100e93  addi         x29, x0, 129  # x29 = 0x00000081
loc_38c:
    38c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    390: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    394: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    398: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    39c: 015a6463  bltu         x20, x21, 0x000003a4  # target 0x000003a4
    3a0: fedff06f  jal          x0, 0x0000038c  # target 0x0000038c
loc_3a4:
    3a4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3a8: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    3ac: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    3b0: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    3b4: 015a6463  bltu         x20, x21, 0x000003bc  # target 0x000003bc
    3b8: fedff06f  jal          x0, 0x000003a4  # target 0x000003a4
loc_3bc:
    3bc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3c0: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    3c4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    3c8: 014a1a13  slli         x20, x20, 20
    3cc: 014a5a13  srli         x20, x20, 20
    3d0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_3d4:
    3d4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    3d8: 000b0463  beq          x22, x0, 0x000003e0  # target 0x000003e0
    3dc: ff9ff06f  jal          x0, 0x000003d4  # target 0x000003d4
loc_3e0:
    3e0: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    3e4: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00012000
    3e8: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    3ec: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    3f0: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    3f4: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    3f8: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write 0x00000081
    3fc: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    400: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    404: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    408: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    40c: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    410: 00c00c13  addi         x24, x0, 12  # x24 = 0x0000000c
    414: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x0000000c
    418: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    41c: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    420: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    424: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    428: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    42c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    430: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_434:
    434: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    438: 000b0463  beq          x22, x0, 0x00000440  # target 0x00000440
    43c: ff9ff06f  jal          x0, 0x00000434  # target 0x00000434
loc_440:
    440: 330000ef  jal          x1, 0x00000770  # target 0x00000770; x1 = 0x00000444
    444: 348000ef  jal          x1, 0x0000078c  # target 0x0000078c; x1 = 0x00000448
    448: 32031263  bne          x6, x0, 0x0000076c  # target 0x0000076c
    44c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    450: 00000413  addi         x8, x0, 0  # x8 = 0x00000000
    454: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    458: 05800713  addi         x14, x0, 88  # x14 = 0x00000058
loc_45c:
    45c: 04e6f463  bgeu         x13, x14, 0x000004a4  # target 0x000004a4
    460: 01000813  addi         x16, x0, 16  # x16 = 0x00000010
    464: 030687b3  mul          x15, x13, x16
    468: 0000fa37  lui          x20, 0x0000f  # x20 = 0x0000f000
    46c: a80a0a13  addi         x20, x20, -1408  # x20 = 0x0000ea80
    470: 014787b3  add          x15, x15, x20
loc_474:
    474: 0087a883  lw           x17, 8(x15)  # Address depends on runtime register values
    478: 00089663  bne          x17, x0, 0x00000484  # target 0x00000484
    47c: 0ff0000f  fence        0xf, 0xf
    480: ff5ff06f  jal          x0, 0x00000474  # target 0x00000474
loc_484:
    484: 0007a903  lw           x18, 0(x15)  # Address depends on runtime register values
    488: 0047a983  lw           x19, 4(x15)  # Address depends on runtime register values
    48c: 0007a423  sw           x0, 8(x15)  # Address depends on runtime register values
    490: 0123f663  bgeu         x7, x18, 0x0000049c  # target 0x0000049c
    494: 00090393  addi         x7, x18, 0
    498: 00098413  addi         x8, x19, 0
loc_49c:
    49c: 00168693  addi         x13, x13, 1
    4a0: fbdff06f  jal          x0, 0x0000045c  # target 0x0000045c
loc_4a4:
    4a4: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    4a8: 0086a023  sw           x8, 0(x13)  # TensixL1.KERNEL_CACHE_BASE · 0x00012000; write runtime value
    4ac: 78400813  addi         x16, x0, 1924  # x16 = 0x00000784
    4b0: 00082683  lw           x13, 0(x16)  # param argmax_host_address; 0x00000784
    4b4: 78800813  addi         x16, x0, 1928  # x16 = 0x00000788
    4b8: 00082703  lw           x14, 0(x16)  # param write_pos; 0x00000788
    4bc: 00471793  slli         x15, x14, 4
    4c0: 00f686b3  add          x13, x13, x15
    4c4: 2ac000ef  jal          x1, 0x00000770  # target 0x00000770; x1 = 0x000004c8
    4c8: 2c4000ef  jal          x1, 0x0000078c  # target 0x0000078c; x1 = 0x000004cc
    4cc: 00012fb7  lui          x31, 0x00012  # x31 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    4d0: 00068f13  addi         x30, x13, 0
    4d4: 01000eb7  lui          x29, 0x01000  # x29 = 0x01000000
    4d8: 613e8e93  addi         x29, x29, 1555  # x29 = 0x01000613 · CQConfig.PCIE_COORD
loc_4dc:
    4dc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4e0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    4e4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    4e8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    4ec: 015a6463  bltu         x20, x21, 0x000004f4  # target 0x000004f4
    4f0: fedff06f  jal          x0, 0x000004dc  # target 0x000004dc
loc_4f4:
    4f4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4f8: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    4fc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    500: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    504: 015a6463  bltu         x20, x21, 0x0000050c  # target 0x0000050c
    508: fedff06f  jal          x0, 0x000004f4  # target 0x000004f4
loc_50c:
    50c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    510: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    514: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    518: 014a1a13  slli         x20, x20, 20
    51c: 014a5a13  srli         x20, x20, 20
    520: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_524:
    524: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    528: 000b0463  beq          x22, x0, 0x00000530  # target 0x00000530
    52c: ff9ff06f  jal          x0, 0x00000524  # target 0x00000524
loc_530:
    530: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    534: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00012000
    538: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    53c: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    540: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    544: 10000c37  lui          x24, 0x10000  # x24 = 0x10000000 · CQConfig.PCIE_MID
    548: 018ba823  sw           x24, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x10000000
    54c: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write 0x01000613
    550: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    554: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    558: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    55c: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    560: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    564: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    568: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000010
    56c: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    570: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    574: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    578: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    57c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    580: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    584: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_588:
    588: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    58c: 000b0463  beq          x22, x0, 0x00000594  # target 0x00000594
    590: ff9ff06f  jal          x0, 0x00000588  # target 0x00000588
loc_594:
    594: 1dc000ef  jal          x1, 0x00000770  # target 0x00000770; x1 = 0x00000598
    598: 1f4000ef  jal          x1, 0x0000078c  # target 0x0000078c; x1 = 0x0000059c
    59c: 78c00893  addi         x17, x0, 1932  # x17 = 0x0000078c
    5a0: 0008a803  lw           x16, 0(x17)  # param write_token; 0x0000078c
    5a4: 1c080463  beq          x16, x0, 0x0000076c  # target 0x0000076c
    5a8: 78800893  addi         x17, x0, 1928  # x17 = 0x00000788
    5ac: 0008a683  lw           x13, 0(x17)  # param write_pos; 0x00000788
    5b0: 00a6d713  srli         x14, x13, 10
    5b4: 3ff6f793  andi         x15, x13, 1023
    5b8: 00070f93  addi         x31, x14, 0
    5bc: 2e0000ef  jal          x1, 0x0000089c  # target 0x0000089c; x1 = 0x000005c0
    5c0: 000a8893  addi         x17, x21, 0
    5c4: 000b0913  addi         x18, x22, 0
    5c8: 1a8000ef  jal          x1, 0x00000770  # target 0x00000770; x1 = 0x000005cc
    5cc: 1c0000ef  jal          x1, 0x0000078c  # target 0x0000078c; x1 = 0x000005d0
    5d0: 00088f93  addi         x31, x17, 0
    5d4: 00090f13  addi         x30, x18, 0
    5d8: 00011eb7  lui          x29, 0x00011  # x29 = 0x00011000
loc_5dc:
    5dc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5e0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    5e4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    5e8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    5ec: 015a6463  bltu         x20, x21, 0x000005f4  # target 0x000005f4
    5f0: fedff06f  jal          x0, 0x000005dc  # target 0x000005dc
loc_5f4:
    5f4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5f8: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    5fc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    600: 014a1a13  slli         x20, x20, 20
    604: 014a5a13  srli         x20, x20, 20
    608: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_60c:
    60c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    610: 000b0463  beq          x22, x0, 0x00000618  # target 0x00000618
    614: ff9ff06f  jal          x0, 0x0000060c  # target 0x0000060c
loc_618:
    618: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    61c: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    620: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    624: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    628: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write 0x00011000
    62c: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    630: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    634: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    638: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    63c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    640: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    644: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    648: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    64c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
    650: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    654: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    658: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    65c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    660: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    664: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    668: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_66c:
    66c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    670: 000b0463  beq          x22, x0, 0x00000678  # target 0x00000678
    674: ff9ff06f  jal          x0, 0x0000066c  # target 0x0000066c
loc_678:
    678: 114000ef  jal          x1, 0x0000078c  # target 0x0000078c; x1 = 0x0000067c
    67c: 00279793  slli         x15, x15, 2
    680: 000118b7  lui          x17, 0x00011  # x17 = 0x00011000
    684: 011787b3  add          x15, x15, x17
    688: 0087a023  sw           x8, 0(x15)  # Address depends on runtime register values
    68c: 00070f93  addi         x31, x14, 0
    690: 20c000ef  jal          x1, 0x0000089c  # target 0x0000089c; x1 = 0x00000694
    694: 000a8893  addi         x17, x21, 0
    698: 000b0913  addi         x18, x22, 0
    69c: 0d4000ef  jal          x1, 0x00000770  # target 0x00000770; x1 = 0x000006a0
    6a0: 0ec000ef  jal          x1, 0x0000078c  # target 0x0000078c; x1 = 0x000006a4
    6a4: 00011fb7  lui          x31, 0x00011  # x31 = 0x00011000
    6a8: 00088f13  addi         x30, x17, 0
    6ac: 00090e93  addi         x29, x18, 0
loc_6b0:
    6b0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    6b4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    6b8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    6bc: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    6c0: 015a6463  bltu         x20, x21, 0x000006c8  # target 0x000006c8
    6c4: fedff06f  jal          x0, 0x000006b0  # target 0x000006b0
loc_6c8:
    6c8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    6cc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    6d0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    6d4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    6d8: 015a6463  bltu         x20, x21, 0x000006e0  # target 0x000006e0
    6dc: fedff06f  jal          x0, 0x000006c8  # target 0x000006c8
loc_6e0:
    6e0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    6e4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    6e8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    6ec: 014a1a13  slli         x20, x20, 20
    6f0: 014a5a13  srli         x20, x20, 20
    6f4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_6f8:
    6f8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    6fc: 000b0463  beq          x22, x0, 0x00000704  # target 0x00000704
    700: ff9ff06f  jal          x0, 0x000006f8  # target 0x000006f8
loc_704:
    704: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    708: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00011000
    70c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    710: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    714: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    718: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    71c: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    720: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    724: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    728: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    72c: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    730: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    734: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    738: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
    73c: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    740: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    744: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    748: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    74c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    750: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    754: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_758:
    758: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    75c: 000b0463  beq          x22, x0, 0x00000764  # target 0x00000764
    760: ff9ff06f  jal          x0, 0x00000758  # target 0x00000758
loc_764:
    764: 00c000ef  jal          x1, 0x00000770  # target 0x00000770; x1 = 0x00000768
    768: 024000ef  jal          x1, 0x0000078c  # target 0x0000078c; x1 = 0x0000076c
loc_76c:
    76c: 17c0006f  jal          x0, 0x000008e8  # target 0x000008e8
loc_770:
    770: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    774: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    778: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    77c: 000a0463  beq          x20, x0, 0x00000784  # target 0x00000784
    780: ff1ff06f  jal          x0, 0x00000770  # target 0x00000770
loc_784:
    784: 0ff0000f  fence        0xf, 0xf
    788: 00008067  jalr         x0, 0(x1)
loc_78c:
    78c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    790: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    794: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    798: 000a0463  beq          x20, x0, 0x000007a0  # target 0x000007a0
    79c: ff1ff06f  jal          x0, 0x0000078c  # target 0x0000078c
loc_7a0:
    7a0: 0ff0000f  fence        0xf, 0xf
    7a4: 00008067  jalr         x0, 0(x1)
loc_7a8:
    7a8: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    7ac: a00a8a93  addi         x21, x21, -1536  # x21 = 0x0000ea00
    7b0: 000aaa03  lw           x20, 0(x21)  # param e2e_logits; 0x0000ea00
    7b4: 007a7d13  andi         x26, x20, 7
    7b8: ff8a7a13  andi         x20, x20, -8
    7bc: 01af8ab3  add          x21, x31, x26
    7c0: 007afb93  andi         x23, x21, 7
    7c4: 003ada93  srli         x21, x21, 3
    7c8: 00ba9a93  slli         x21, x21, 11
    7cc: 014a8ab3  add          x21, x21, x20
    7d0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000007d0
    7d4: 018b0b13  addi         x22, x22, 24  # x22 = 0x000007e8
    7d8: 001b9b93  slli         x23, x23, 1
    7dc: 017b0b33  add          x22, x22, x23
    7e0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    7e4: 00008067  jalr         x0, 0(x1)
    7e8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    7ec: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7f0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    7f4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_7f8:
    7f8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    7fc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    800: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    804: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    808: 015a6463  bltu         x20, x21, 0x00000810  # target 0x00000810
    80c: fedff06f  jal          x0, 0x000007f8  # target 0x000007f8
loc_810:
    810: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    814: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    818: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    81c: 014a1a13  slli         x20, x20, 20
    820: 014a5a13  srli         x20, x20, 20
    824: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_828:
    828: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    82c: 000b0463  beq          x22, x0, 0x00000834  # target 0x00000834
    830: ff9ff06f  jal          x0, 0x00000828  # target 0x00000828
loc_834:
    834: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    838: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    83c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    840: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    844: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    848: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    84c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    850: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    854: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    858: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    85c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    860: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    864: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    868: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    86c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    870: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    874: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    878: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    87c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    880: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    884: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    888: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_88c:
    88c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    890: 000b0463  beq          x22, x0, 0x00000898  # target 0x00000898
    894: ff9ff06f  jal          x0, 0x0000088c  # target 0x0000088c
loc_898:
    898: 00008067  jalr         x0, 0(x1)
loc_89c:
    89c: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    8a0: 000aaa03  lw           x20, 0(x21)  # param e2e_token_history; 0x00000780
    8a4: 007a7d13  andi         x26, x20, 7
    8a8: ff8a7a13  andi         x20, x20, -8
    8ac: 01af8ab3  add          x21, x31, x26
    8b0: 007afb93  andi         x23, x21, 7
    8b4: 003ada93  srli         x21, x21, 3
    8b8: 00ca9a93  slli         x21, x21, 12
    8bc: 014a8ab3  add          x21, x21, x20
    8c0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000008c0
    8c4: 018b0b13  addi         x22, x22, 24  # x22 = 0x000008d8
    8c8: 001b9b93  slli         x23, x23, 1
    8cc: 017b0b33  add          x22, x22, x23
    8d0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    8d4: 00008067  jalr         x0, 0(x1)
    8d8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    8dc: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    8e0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    8e4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    8e8:           j FW_BRISC+4   # return to firmware, linked at install
