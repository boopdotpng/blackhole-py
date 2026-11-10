# llama3 8b-fp8 decode: argmax, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_token_history, 0x784=argmax_host_address, 0x788=argmax_count, 0x78c=write_pos, 0x790=write_token, 0xea00=e2e_logits, 0xea04=argmax_start, 0xea08=argmax_core
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
      c: 04028293  addi         x5, x5, 64  # x5 = 0x0000f040
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0000f040
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     24: 88038393  addi         x7, x7, -1920  # x7 = 0xffb00880 · riscv_local_mem + 0x880
     28: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
     2c: 04040413  addi         x8, x8, 64  # x8 = 0x00010040
     30: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00010040
     34: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     38: 88438393  addi         x7, x7, -1916  # x7 = 0xffb00884 · riscv_local_mem + 0x884
     3c: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     40: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     44: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     48: 0004a203  lw           x4, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_4c:
     4c: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
     50: 02048493  addi         x9, x9, 32  # x9 = 0xffb48020
     54: 0004d283  lhu          x5, 0(x9)  # 0xffb48020
     58: 40520333  sub          x6, x4, x5
     5c: 01031313  slli         x6, x6, 16
     60: 01035313  srli         x6, x6, 16
     64: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
     68: 406383b3  sub          x7, x7, x6
     6c: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
     70: 0083f663  bgeu         x7, x8, 0x0000007c  # target 0x0000007c
     74: 0ff0000f  fence        0xf, 0xf
     78: fd5ff06f  jal          x0, 0x0000004c  # target 0x0000004c
loc_7c:
     7c: 0ff0000f  fence        0xf, 0xf
     80: 6b0000ef  jal          x1, 0x00000730  # target 0x00000730; x1 = 0x00000084
     84: 6c8000ef  jal          x1, 0x0000074c  # target 0x0000074c; x1 = 0x00000088
     88: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     8c: 6dc000ef  jal          x1, 0x00000768  # target 0x00000768; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
     a4: 040e8e93  addi         x29, x29, 64  # x29 = 0x0000f040
     a8: 710000ef  jal          x1, 0x000007b8  # target 0x000007b8; x1 = 0x000000ac
     ac: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     b0: 6b8000ef  jal          x1, 0x00000768  # target 0x00000768; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 00010eb7  lui          x29, 0x00010  # x29 = 0x00010000
     c8: 840e8e93  addi         x29, x29, -1984  # x29 = 0x0000f840
     cc: 6ec000ef  jal          x1, 0x000007b8  # target 0x000007b8; x1 = 0x000000d0
     d0: 67c000ef  jal          x1, 0x0000074c  # target 0x0000074c; x1 = 0x000000d4
     d4: 78800393  addi         x7, x0, 1928  # x7 = 0x00000788
     d8: 0003a203  lw           x4, 0(x7)  # param argmax_count; 0x00000788
     dc: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
     e0: a0438393  addi         x7, x7, -1532  # x7 = 0x0000ea04
     e4: 0003a283  lw           x5, 0(x7)  # param argmax_start; 0x0000ea04
     e8: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
     ec: a0838393  addi         x7, x7, -1528  # x7 = 0x0000ea08
     f0: 0003a303  lw           x6, 0(x7)  # param argmax_core; 0x0000ea08
     f4: 53800393  addi         x7, x0, 1336  # x7 = 0x00000538
     f8: 04721e63  bne          x4, x7, 0x00000154  # target 0x00000154
     fc: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
    100: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
    104: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
    108: 98040413  addi         x8, x8, -1664  # x8 = 0x0000f980
    10c: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    110: 03000593  addi         x11, x0, 48  # x11 = 0x00000030
loc_114:
    114: 00b57a63  bgeu         x10, x11, 0x00000128  # target 0x00000128
    118: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    11c: 00440413  addi         x8, x8, 4
    120: 00150513  addi         x10, x10, 1
    124: ff1ff06f  jal          x0, 0x00000114  # target 0x00000114
loc_128:
    128: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
    12c: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
    130: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
    134: b7040413  addi         x8, x8, -1168  # x8 = 0x0000fb70
    138: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    13c: 13400593  addi         x11, x0, 308  # x11 = 0x00000134
loc_140:
    140: 00b57a63  bgeu         x10, x11, 0x00000154  # target 0x00000154
    144: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    148: 00440413  addi         x8, x8, 4
    14c: 00150513  addi         x10, x10, 1
    150: ff1ff06f  jal          x0, 0x00000140  # target 0x00000140
loc_154:
    154: 0ff0000f  fence        0xf, 0xf
    158: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    15c: 87858593  addi         x11, x11, -1928  # x11 = 0xffb00878 · riscv_local_mem + 0x878
    160: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x878 · 0xffb00878
    164: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    168: 008383b3  add          x7, x7, x8
    16c: 000104b7  lui          x9, 0x00010  # x9 = 0x00010000
    170: 04048493  addi         x9, x9, 64  # x9 = 0x00010040
    174: 0093e663  bltu         x7, x9, 0x00000180  # target 0x00000180
    178: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    17c: 40a383b3  sub          x7, x7, x10
loc_180:
    180: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    184: 87858593  addi         x11, x11, -1928  # x11 = 0xffb00878 · riscv_local_mem + 0x878
    188: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    18c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    190: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    194: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    198: 00238393  addi         x7, x7, 2
    19c: 01039393  slli         x7, x7, 16
    1a0: 0103d393  srli         x7, x7, 16
    1a4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1a8: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    1ac: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1b0: ffb48437  lui          x8, 0xffb48  # x8 = 0xffb48000
    1b4: 02840413  addi         x8, x8, 40  # x8 = 0xffb48028
    1b8: 00742023  sw           x7, 0(x8)  # 0xffb48028; write runtime value
    1bc: 0ff0000f  fence        0xf, 0xf
    1c0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1c4: 88458593  addi         x11, x11, -1916  # x11 = 0xffb00884 · riscv_local_mem + 0x884
    1c8: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x884 · 0xffb00884
    1cc: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_1d0:
    1d0: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
    1d4: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
    1d8: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
    1dc: 407404b3  sub          x9, x8, x7
    1e0: 01049493  slli         x9, x9, 16
    1e4: 0104d493  srli         x9, x9, 16
    1e8: 00a4f663  bgeu         x9, x10, 0x000001f4  # target 0x000001f4
    1ec: 0ff0000f  fence        0xf, 0xf
    1f0: fe1ff06f  jal          x0, 0x000001d0  # target 0x000001d0
loc_1f4:
    1f4: 0ff0000f  fence        0xf, 0xf
    1f8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1fc: 80000437  lui          x8, 0x80000  # x8 = 0x80000000 · arc_apb + 0x0
    200: fff40413  addi         x8, x8, -1  # x8 = 0x7fffffff
    204: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    208: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    20c: 0006a583  lw           x11, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    210: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    214: 02000713  addi         x14, x0, 32  # x14 = 0x00000020
loc_218:
    218: 06e6f263  bgeu         x13, x14, 0x0000027c  # target 0x0000027c
    21c: 0005a483  lw           x9, 0(x11)  # Address depends on runtime register values
    220: 00f4d493  srli         x9, x9, 15
    224: 0045a603  lw           x12, 4(x11)  # Address depends on runtime register values
    228: c0067513  andi         x10, x12, -1024
    22c: 20067793  andi         x15, x12, 512
    230: 00f56533  or           x10, x10, x15
    234: 10067793  andi         x15, x12, 256
    238: 0047d793  srli         x15, x15, 4
    23c: 00f56533  or           x10, x10, x15
    240: 0f067793  andi         x15, x12, 240
    244: 00179793  slli         x15, x15, 1
    248: 00f56533  or           x10, x10, x15
    24c: 00f67793  andi         x15, x12, 15
    250: 00f56533  or           x10, x10, x15
    254: 00858593  addi         x11, x11, 8
    258: 00457e63  bgeu         x10, x4, 0x00000274  # target 0x00000274
    25c: 00a28533  add          x10, x5, x10
    260: 0093e663  bltu         x7, x9, 0x0000026c  # target 0x0000026c
    264: 00939863  bne          x7, x9, 0x00000274  # target 0x00000274
    268: 00857663  bgeu         x10, x8, 0x00000274  # target 0x00000274
loc_26c:
    26c: 00048393  addi         x7, x9, 0
    270: 00050413  addi         x8, x10, 0
loc_274:
    274: 00168693  addi         x13, x13, 1
    278: fa1ff06f  jal          x0, 0x00000218  # target 0x00000218
loc_27c:
    27c: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    280: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    284: 00072683  lw           x13, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
    288: 00168693  addi         x13, x13, 1
    28c: 01069693  slli         x13, x13, 16
    290: 0106d693  srli         x13, x13, 16
    294: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    298: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    29c: 00d72023  sw           x13, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    2a0: ffb49737  lui          x14, 0xffb49  # x14 = 0xffb49000
    2a4: 02070713  addi         x14, x14, 32  # x14 = 0xffb49020
    2a8: 00d72023  sw           x13, 0(x14)  # 0xffb49020; write runtime value
    2ac: 0ff0000f  fence        0xf, 0xf
    2b0: ffb018b7  lui          x17, 0xffb01  # x17 = 0xffb01000
    2b4: 88088893  addi         x17, x17, -1920  # x17 = 0xffb00880 · riscv_local_mem + 0x880
    2b8: 0008a683  lw           x13, 0(x17)  # riscv_local_mem + 0x880 · 0xffb00880
    2bc: 00001737  lui          x14, 0x00001  # x14 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2c0: 00e686b3  add          x13, x13, x14
    2c4: 000117b7  lui          x15, 0x00011  # x15 = 0x00011000
    2c8: 04078793  addi         x15, x15, 64  # x15 = 0x00011040
    2cc: 00f6e663  bltu         x13, x15, 0x000002d8  # target 0x000002d8
    2d0: 00001837  lui          x16, 0x00001  # x16 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2d4: 410686b3  sub          x13, x13, x16
loc_2d8:
    2d8: ffb018b7  lui          x17, 0xffb01  # x17 = 0xffb01000
    2dc: 88088893  addi         x17, x17, -1920  # x17 = 0xffb00880 · riscv_local_mem + 0x880
    2e0: 00d8a023  sw           x13, 0(x17)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    2e4: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2e8: 04068693  addi         x13, x13, 64  # x13 = 0x00012040
    2ec: 0076a023  sw           x7, 0(x13)  # 0x00012040; write runtime value
    2f0: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2f4: 04468693  addi         x13, x13, 68  # x13 = 0x00012044
    2f8: 0086a023  sw           x8, 0(x13)  # 0x00012044; write runtime value
    2fc: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    300: 04868693  addi         x13, x13, 72  # x13 = 0x00012048
    304: 00100713  addi         x14, x0, 1  # x14 = 0x00000001
    308: 00e6a023  sw           x14, 0(x13)  # 0x00012048; write 0x00000001
    30c: 01000713  addi         x14, x0, 16  # x14 = 0x00000010
    310: 02e306b3  mul          x13, x6, x14
    314: 0000f7b7  lui          x15, 0x0000f  # x15 = 0x0000f000
    318: a4078793  addi         x15, x15, -1472  # x15 = 0x0000ea40
    31c: 00f686b3  add          x13, x13, x15
    320: 410000ef  jal          x1, 0x00000730  # target 0x00000730; x1 = 0x00000324
    324: 428000ef  jal          x1, 0x0000074c  # target 0x0000074c; x1 = 0x00000328
    328: 00012fb7  lui          x31, 0x00012  # x31 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    32c: 040f8f93  addi         x31, x31, 64  # x31 = 0x00012040
    330: 00068f13  addi         x30, x13, 0
    334: 08100e93  addi         x29, x0, 129  # x29 = 0x00000081
loc_338:
    338: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    33c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    340: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    344: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    348: 015a6463  bltu         x20, x21, 0x00000350  # target 0x00000350
    34c: fedff06f  jal          x0, 0x00000338  # target 0x00000338
loc_350:
    350: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    354: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    358: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    35c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    360: 015a6463  bltu         x20, x21, 0x00000368  # target 0x00000368
    364: fedff06f  jal          x0, 0x00000350  # target 0x00000350
loc_368:
    368: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    36c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    370: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    374: 014a1a13  slli         x20, x20, 20
    378: 014a5a13  srli         x20, x20, 20
    37c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_380:
    380: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    384: 000b0463  beq          x22, x0, 0x0000038c  # target 0x0000038c
    388: ff9ff06f  jal          x0, 0x00000380  # target 0x00000380
loc_38c:
    38c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    390: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00012040
    394: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    398: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    39c: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    3a0: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    3a4: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write 0x00000081
    3a8: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    3ac: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    3b0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    3b4: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    3b8: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    3bc: 00c00c13  addi         x24, x0, 12  # x24 = 0x0000000c
    3c0: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x0000000c
    3c4: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    3c8: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    3cc: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    3d0: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    3d4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    3d8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    3dc: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_3e0:
    3e0: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    3e4: 000b0463  beq          x22, x0, 0x000003ec  # target 0x000003ec
    3e8: ff9ff06f  jal          x0, 0x000003e0  # target 0x000003e0
loc_3ec:
    3ec: 344000ef  jal          x1, 0x00000730  # target 0x00000730; x1 = 0x000003f0
    3f0: 35c000ef  jal          x1, 0x0000074c  # target 0x0000074c; x1 = 0x000003f4
    3f4: 32031c63  bne          x6, x0, 0x0000072c  # target 0x0000072c
    3f8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    3fc: 00000413  addi         x8, x0, 0  # x8 = 0x00000000
    400: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    404: 06000713  addi         x14, x0, 96  # x14 = 0x00000060
loc_408:
    408: 04e6f463  bgeu         x13, x14, 0x00000450  # target 0x00000450
    40c: 01000813  addi         x16, x0, 16  # x16 = 0x00000010
    410: 030687b3  mul          x15, x13, x16
    414: 0000fa37  lui          x20, 0x0000f  # x20 = 0x0000f000
    418: a40a0a13  addi         x20, x20, -1472  # x20 = 0x0000ea40
    41c: 014787b3  add          x15, x15, x20
loc_420:
    420: 0087a883  lw           x17, 8(x15)  # Address depends on runtime register values
    424: 00089663  bne          x17, x0, 0x00000430  # target 0x00000430
    428: 0ff0000f  fence        0xf, 0xf
    42c: ff5ff06f  jal          x0, 0x00000420  # target 0x00000420
loc_430:
    430: 0007a903  lw           x18, 0(x15)  # Address depends on runtime register values
    434: 0047a983  lw           x19, 4(x15)  # Address depends on runtime register values
    438: 0007a423  sw           x0, 8(x15)  # Address depends on runtime register values
    43c: 0123f663  bgeu         x7, x18, 0x00000448  # target 0x00000448
    440: 00090393  addi         x7, x18, 0
    444: 00098413  addi         x8, x19, 0
loc_448:
    448: 00168693  addi         x13, x13, 1
    44c: fbdff06f  jal          x0, 0x00000408  # target 0x00000408
loc_450:
    450: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    454: 04068693  addi         x13, x13, 64  # x13 = 0x00012040
    458: 0086a023  sw           x8, 0(x13)  # 0x00012040; write runtime value
    45c: 78400813  addi         x16, x0, 1924  # x16 = 0x00000784
    460: 00082683  lw           x13, 0(x16)  # param argmax_host_address; 0x00000784
    464: 78c00813  addi         x16, x0, 1932  # x16 = 0x0000078c
    468: 00082703  lw           x14, 0(x16)  # param write_pos; 0x0000078c
    46c: 00471793  slli         x15, x14, 4
    470: 00f686b3  add          x13, x13, x15
    474: 2bc000ef  jal          x1, 0x00000730  # target 0x00000730; x1 = 0x00000478
    478: 2d4000ef  jal          x1, 0x0000074c  # target 0x0000074c; x1 = 0x0000047c
    47c: 00012fb7  lui          x31, 0x00012  # x31 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    480: 040f8f93  addi         x31, x31, 64  # x31 = 0x00012040
    484: 00068f13  addi         x30, x13, 0
    488: 01000eb7  lui          x29, 0x01000  # x29 = 0x01000000
    48c: 613e8e93  addi         x29, x29, 1555  # x29 = 0x01000613 · CQConfig.PCIE_COORD
loc_490:
    490: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    494: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    498: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    49c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    4a0: 015a6463  bltu         x20, x21, 0x000004a8  # target 0x000004a8
    4a4: fedff06f  jal          x0, 0x00000490  # target 0x00000490
loc_4a8:
    4a8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4ac: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    4b0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    4b4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    4b8: 015a6463  bltu         x20, x21, 0x000004c0  # target 0x000004c0
    4bc: fedff06f  jal          x0, 0x000004a8  # target 0x000004a8
loc_4c0:
    4c0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4c4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    4c8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    4cc: 014a1a13  slli         x20, x20, 20
    4d0: 014a5a13  srli         x20, x20, 20
    4d4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_4d8:
    4d8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    4dc: 000b0463  beq          x22, x0, 0x000004e4  # target 0x000004e4
    4e0: ff9ff06f  jal          x0, 0x000004d8  # target 0x000004d8
loc_4e4:
    4e4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    4e8: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00012040
    4ec: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    4f0: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    4f4: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    4f8: 10000c37  lui          x24, 0x10000  # x24 = 0x10000000 · CQConfig.PCIE_MID
    4fc: 018ba823  sw           x24, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x10000000
    500: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write 0x01000613
    504: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    508: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    50c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    510: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    514: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    518: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    51c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000010
    520: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    524: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    528: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    52c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    530: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    534: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    538: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_53c:
    53c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    540: 000b0463  beq          x22, x0, 0x00000548  # target 0x00000548
    544: ff9ff06f  jal          x0, 0x0000053c  # target 0x0000053c
loc_548:
    548: 1e8000ef  jal          x1, 0x00000730  # target 0x00000730; x1 = 0x0000054c
    54c: 200000ef  jal          x1, 0x0000074c  # target 0x0000074c; x1 = 0x00000550
    550: 79000893  addi         x17, x0, 1936  # x17 = 0x00000790
    554: 0008a803  lw           x16, 0(x17)  # param write_token; 0x00000790
    558: 1c080a63  beq          x16, x0, 0x0000072c  # target 0x0000072c
    55c: 78c00893  addi         x17, x0, 1932  # x17 = 0x0000078c
    560: 0008a683  lw           x13, 0(x17)  # param write_pos; 0x0000078c
    564: 00a6d713  srli         x14, x13, 10
    568: 3ff6f793  andi         x15, x13, 1023
    56c: 00070f93  addi         x31, x14, 0
    570: 2ec000ef  jal          x1, 0x0000085c  # target 0x0000085c; x1 = 0x00000574
    574: 000a8893  addi         x17, x21, 0
    578: 000b0913  addi         x18, x22, 0
    57c: 1b4000ef  jal          x1, 0x00000730  # target 0x00000730; x1 = 0x00000580
    580: 1cc000ef  jal          x1, 0x0000074c  # target 0x0000074c; x1 = 0x00000584
    584: 00088f93  addi         x31, x17, 0
    588: 00090f13  addi         x30, x18, 0
    58c: 00011eb7  lui          x29, 0x00011  # x29 = 0x00011000
    590: 040e8e93  addi         x29, x29, 64  # x29 = 0x00011040
loc_594:
    594: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    598: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    59c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    5a0: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    5a4: 015a6463  bltu         x20, x21, 0x000005ac  # target 0x000005ac
    5a8: fedff06f  jal          x0, 0x00000594  # target 0x00000594
loc_5ac:
    5ac: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5b0: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    5b4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    5b8: 014a1a13  slli         x20, x20, 20
    5bc: 014a5a13  srli         x20, x20, 20
    5c0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_5c4:
    5c4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5c8: 000b0463  beq          x22, x0, 0x000005d0  # target 0x000005d0
    5cc: ff9ff06f  jal          x0, 0x000005c4  # target 0x000005c4
loc_5d0:
    5d0: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    5d4: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    5d8: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    5dc: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    5e0: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write 0x00011040
    5e4: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    5e8: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    5ec: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    5f0: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    5f4: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    5f8: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    5fc: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    600: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    604: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
    608: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    60c: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    610: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    614: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    618: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    61c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    620: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_624:
    624: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    628: 000b0463  beq          x22, x0, 0x00000630  # target 0x00000630
    62c: ff9ff06f  jal          x0, 0x00000624  # target 0x00000624
loc_630:
    630: 11c000ef  jal          x1, 0x0000074c  # target 0x0000074c; x1 = 0x00000634
    634: 00279793  slli         x15, x15, 2
    638: 000118b7  lui          x17, 0x00011  # x17 = 0x00011000
    63c: 04088893  addi         x17, x17, 64  # x17 = 0x00011040
    640: 011787b3  add          x15, x15, x17
    644: 0087a023  sw           x8, 0(x15)  # Address depends on runtime register values
    648: 00070f93  addi         x31, x14, 0
    64c: 210000ef  jal          x1, 0x0000085c  # target 0x0000085c; x1 = 0x00000650
    650: 000a8893  addi         x17, x21, 0
    654: 000b0913  addi         x18, x22, 0
    658: 0d8000ef  jal          x1, 0x00000730  # target 0x00000730; x1 = 0x0000065c
    65c: 0f0000ef  jal          x1, 0x0000074c  # target 0x0000074c; x1 = 0x00000660
    660: 00011fb7  lui          x31, 0x00011  # x31 = 0x00011000
    664: 040f8f93  addi         x31, x31, 64  # x31 = 0x00011040
    668: 00088f13  addi         x30, x17, 0
    66c: 00090e93  addi         x29, x18, 0
loc_670:
    670: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    674: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    678: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    67c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    680: 015a6463  bltu         x20, x21, 0x00000688  # target 0x00000688
    684: fedff06f  jal          x0, 0x00000670  # target 0x00000670
loc_688:
    688: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    68c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    690: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    694: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    698: 015a6463  bltu         x20, x21, 0x000006a0  # target 0x000006a0
    69c: fedff06f  jal          x0, 0x00000688  # target 0x00000688
loc_6a0:
    6a0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    6a4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    6a8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    6ac: 014a1a13  slli         x20, x20, 20
    6b0: 014a5a13  srli         x20, x20, 20
    6b4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_6b8:
    6b8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    6bc: 000b0463  beq          x22, x0, 0x000006c4  # target 0x000006c4
    6c0: ff9ff06f  jal          x0, 0x000006b8  # target 0x000006b8
loc_6c4:
    6c4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    6c8: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00011040
    6cc: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    6d0: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    6d4: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    6d8: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    6dc: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    6e0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    6e4: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    6e8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    6ec: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    6f0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    6f4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6f8: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
    6fc: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    700: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    704: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    708: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    70c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    710: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    714: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_718:
    718: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    71c: 000b0463  beq          x22, x0, 0x00000724  # target 0x00000724
    720: ff9ff06f  jal          x0, 0x00000718  # target 0x00000718
loc_724:
    724: 00c000ef  jal          x1, 0x00000730  # target 0x00000730; x1 = 0x00000728
    728: 024000ef  jal          x1, 0x0000074c  # target 0x0000074c; x1 = 0x0000072c
loc_72c:
    72c: 17c0006f  jal          x0, 0x000008a8  # target 0x000008a8
loc_730:
    730: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    734: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    738: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    73c: 000a0463  beq          x20, x0, 0x00000744  # target 0x00000744
    740: ff1ff06f  jal          x0, 0x00000730  # target 0x00000730
loc_744:
    744: 0ff0000f  fence        0xf, 0xf
    748: 00008067  jalr         x0, 0(x1)
loc_74c:
    74c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    750: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    754: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    758: 000a0463  beq          x20, x0, 0x00000760  # target 0x00000760
    75c: ff1ff06f  jal          x0, 0x0000074c  # target 0x0000074c
loc_760:
    760: 0ff0000f  fence        0xf, 0xf
    764: 00008067  jalr         x0, 0(x1)
loc_768:
    768: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    76c: a00a8a93  addi         x21, x21, -1536  # x21 = 0x0000ea00
    770: 000aaa03  lw           x20, 0(x21)  # param e2e_logits; 0x0000ea00
    774: 007a7d13  andi         x26, x20, 7
    778: ff8a7a13  andi         x20, x20, -8
    77c: 01af8ab3  add          x21, x31, x26
    780: 007afb93  andi         x23, x21, 7
    784: 003ada93  srli         x21, x21, 3
    788: 00ba9a93  slli         x21, x21, 11
    78c: 014a8ab3  add          x21, x21, x20
    790: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000790
    794: 018b0b13  addi         x22, x22, 24  # x22 = 0x000007a8
    798: 001b9b93  slli         x23, x23, 1
    79c: 017b0b33  add          x22, x22, x23
    7a0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    7a4: 00008067  jalr         x0, 0(x1)
    7a8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    7ac: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7b0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    7b4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_7b8:
    7b8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    7bc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    7c0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    7c4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    7c8: 015a6463  bltu         x20, x21, 0x000007d0  # target 0x000007d0
    7cc: fedff06f  jal          x0, 0x000007b8  # target 0x000007b8
loc_7d0:
    7d0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    7d4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    7d8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    7dc: 014a1a13  slli         x20, x20, 20
    7e0: 014a5a13  srli         x20, x20, 20
    7e4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_7e8:
    7e8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    7ec: 000b0463  beq          x22, x0, 0x000007f4  # target 0x000007f4
    7f0: ff9ff06f  jal          x0, 0x000007e8  # target 0x000007e8
loc_7f4:
    7f4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    7f8: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    7fc: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    800: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    804: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    808: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    80c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    810: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    814: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    818: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    81c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    820: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    824: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    828: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    82c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    830: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    834: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    838: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    83c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    840: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    844: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    848: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_84c:
    84c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    850: 000b0463  beq          x22, x0, 0x00000858  # target 0x00000858
    854: ff9ff06f  jal          x0, 0x0000084c  # target 0x0000084c
loc_858:
    858: 00008067  jalr         x0, 0(x1)
loc_85c:
    85c: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    860: 000aaa03  lw           x20, 0(x21)  # param e2e_token_history; 0x00000780
    864: 007a7d13  andi         x26, x20, 7
    868: ff8a7a13  andi         x20, x20, -8
    86c: 01af8ab3  add          x21, x31, x26
    870: 007afb93  andi         x23, x21, 7
    874: 003ada93  srli         x21, x21, 3
    878: 00ca9a93  slli         x21, x21, 12
    87c: 014a8ab3  add          x21, x21, x20
    880: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000880
    884: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000898
    888: 001b9b93  slli         x23, x23, 1
    88c: 017b0b33  add          x22, x22, x23
    890: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    894: 00008067  jalr         x0, 0(x1)
    898: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    89c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    8a0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    8a4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    8a8:           j FW_BRISC+4   # return to firmware, linked at install
