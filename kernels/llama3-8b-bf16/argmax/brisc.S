# llama3 8b-bf16 decode: argmax, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9
# params: 0x780=e2e_token_history, 0x784=argmax_host_address, 0x788=write_pos, 0x78c=write_token, 0xea00=e2e_logits, 0xea04=argmax_start, 0xea08=argmax_count, 0xea0c=argmax_core
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
      c: fc028293  addi         x5, x5, -64  # x5 = 0x0000efc0
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0000efc0
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     24: 88038393  addi         x7, x7, -1920  # x7 = 0xffb00880 · riscv_local_mem + 0x880
     28: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
     2c: fc040413  addi         x8, x8, -64  # x8 = 0x0000ffc0
     30: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x0000ffc0
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
     80: 720000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x00000084
     84: 738000ef  jal          x1, 0x000007bc  # target 0x000007bc; x1 = 0x00000088
     88: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     8c: 74c000ef  jal          x1, 0x000007d8  # target 0x000007d8; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
     a4: fc0e8e93  addi         x29, x29, -64  # x29 = 0x0000efc0
     a8: 780000ef  jal          x1, 0x00000828  # target 0x00000828; x1 = 0x000000ac
     ac: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     b0: 728000ef  jal          x1, 0x000007d8  # target 0x000007d8; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
     c8: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x0000f7c0
     cc: 75c000ef  jal          x1, 0x00000828  # target 0x00000828; x1 = 0x000000d0
     d0: 6ec000ef  jal          x1, 0x000007bc  # target 0x000007bc; x1 = 0x000000d4
     d4: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
     d8: a0838393  addi         x7, x7, -1528  # x7 = 0x0000ea08
     dc: 0003a203  lw           x4, 0(x7)  # param argmax_count; 0x0000ea08
     e0: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
     e4: a0438393  addi         x7, x7, -1532  # x7 = 0x0000ea04
     e8: 0003a283  lw           x5, 0(x7)  # param argmax_start; 0x0000ea04
     ec: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
     f0: a0c38393  addi         x7, x7, -1524  # x7 = 0x0000ea0c
     f4: 0003a303  lw           x6, 0(x7)  # param argmax_core; 0x0000ea0c
     f8: 5b100393  addi         x7, x0, 1457  # x7 = 0x000005b1
     fc: 06721463  bne          x4, x7, 0x00000164  # target 0x00000164
    100: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
    104: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
    108: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
    10c: 98040413  addi         x8, x8, -1664  # x8 = 0x0000f980
    110: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    114: 01000593  addi         x11, x0, 16  # x11 = 0x00000010
loc_118:
    118: 00b57a63  bgeu         x10, x11, 0x0000012c  # target 0x0000012c
    11c: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    120: 00440413  addi         x8, x8, 4
    124: 00150513  addi         x10, x10, 1
    128: ff1ff06f  jal          x0, 0x00000118  # target 0x00000118
loc_12c:
    12c: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
    130: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
    134: 00010537  lui          x10, 0x00010  # x10 = 0x00010000
    138: b6250513  addi         x10, x10, -1182  # x10 = 0x0000fb62
    13c: 00951023  sh           x9, 0(x10)  # 0x0000fb62; write 0x0000ff80
    140: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
    144: b6440413  addi         x8, x8, -1180  # x8 = 0x0000fb64
    148: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    14c: 11700593  addi         x11, x0, 279  # x11 = 0x00000117
loc_150:
    150: 00b57a63  bgeu         x10, x11, 0x00000164  # target 0x00000164
    154: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    158: 00440413  addi         x8, x8, 4
    15c: 00150513  addi         x10, x10, 1
    160: ff1ff06f  jal          x0, 0x00000150  # target 0x00000150
loc_164:
    164: 5b200393  addi         x7, x0, 1458  # x7 = 0x000005b2
    168: 04721e63  bne          x4, x7, 0x000001c4  # target 0x000001c4
    16c: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
    170: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
    174: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
    178: 98040413  addi         x8, x8, -1664  # x8 = 0x0000f980
    17c: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    180: 01000593  addi         x11, x0, 16  # x11 = 0x00000010
loc_184:
    184: 00b57a63  bgeu         x10, x11, 0x00000198  # target 0x00000198
    188: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    18c: 00440413  addi         x8, x8, 4
    190: 00150513  addi         x10, x10, 1
    194: ff1ff06f  jal          x0, 0x00000184  # target 0x00000184
loc_198:
    198: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
    19c: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
    1a0: 00010437  lui          x8, 0x00010  # x8 = 0x00010000
    1a4: b6440413  addi         x8, x8, -1180  # x8 = 0x0000fb64
    1a8: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    1ac: 11700593  addi         x11, x0, 279  # x11 = 0x00000117
loc_1b0:
    1b0: 00b57a63  bgeu         x10, x11, 0x000001c4  # target 0x000001c4
    1b4: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    1b8: 00440413  addi         x8, x8, 4
    1bc: 00150513  addi         x10, x10, 1
    1c0: ff1ff06f  jal          x0, 0x000001b0  # target 0x000001b0
loc_1c4:
    1c4: 0ff0000f  fence        0xf, 0xf
    1c8: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1cc: 87858593  addi         x11, x11, -1928  # x11 = 0xffb00878 · riscv_local_mem + 0x878
    1d0: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x878 · 0xffb00878
    1d4: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1d8: 008383b3  add          x7, x7, x8
    1dc: 000104b7  lui          x9, 0x00010  # x9 = 0x00010000
    1e0: fc048493  addi         x9, x9, -64  # x9 = 0x0000ffc0
    1e4: 0093e663  bltu         x7, x9, 0x000001f0  # target 0x000001f0
    1e8: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1ec: 40a383b3  sub          x7, x7, x10
loc_1f0:
    1f0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1f4: 87858593  addi         x11, x11, -1928  # x11 = 0xffb00878 · riscv_local_mem + 0x878
    1f8: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1fc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    200: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    204: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    208: 00238393  addi         x7, x7, 2
    20c: 01039393  slli         x7, x7, 16
    210: 0103d393  srli         x7, x7, 16
    214: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    218: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    21c: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    220: ffb48437  lui          x8, 0xffb48  # x8 = 0xffb48000
    224: 02840413  addi         x8, x8, 40  # x8 = 0xffb48028
    228: 00742023  sw           x7, 0(x8)  # 0xffb48028; write runtime value
    22c: 0ff0000f  fence        0xf, 0xf
    230: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    234: 88458593  addi         x11, x11, -1916  # x11 = 0xffb00884 · riscv_local_mem + 0x884
    238: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x884 · 0xffb00884
    23c: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_240:
    240: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
    244: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
    248: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
    24c: 407404b3  sub          x9, x8, x7
    250: 01049493  slli         x9, x9, 16
    254: 0104d493  srli         x9, x9, 16
    258: 00a4f663  bgeu         x9, x10, 0x00000264  # target 0x00000264
    25c: 0ff0000f  fence        0xf, 0xf
    260: fe1ff06f  jal          x0, 0x00000240  # target 0x00000240
loc_264:
    264: 0ff0000f  fence        0xf, 0xf
    268: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    26c: 80000437  lui          x8, 0x80000  # x8 = 0x80000000 · arc_apb + 0x0
    270: fff40413  addi         x8, x8, -1  # x8 = 0x7fffffff
    274: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    278: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    27c: 0006a583  lw           x11, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    280: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    284: 02000713  addi         x14, x0, 32  # x14 = 0x00000020
loc_288:
    288: 06e6f263  bgeu         x13, x14, 0x000002ec  # target 0x000002ec
    28c: 0005a483  lw           x9, 0(x11)  # Address depends on runtime register values
    290: 00f4d493  srli         x9, x9, 15
    294: 0045a603  lw           x12, 4(x11)  # Address depends on runtime register values
    298: c0067513  andi         x10, x12, -1024
    29c: 20067793  andi         x15, x12, 512
    2a0: 00f56533  or           x10, x10, x15
    2a4: 10067793  andi         x15, x12, 256
    2a8: 0047d793  srli         x15, x15, 4
    2ac: 00f56533  or           x10, x10, x15
    2b0: 0f067793  andi         x15, x12, 240
    2b4: 00179793  slli         x15, x15, 1
    2b8: 00f56533  or           x10, x10, x15
    2bc: 00f67793  andi         x15, x12, 15
    2c0: 00f56533  or           x10, x10, x15
    2c4: 00858593  addi         x11, x11, 8
    2c8: 00457e63  bgeu         x10, x4, 0x000002e4  # target 0x000002e4
    2cc: 00a28533  add          x10, x5, x10
    2d0: 0093e663  bltu         x7, x9, 0x000002dc  # target 0x000002dc
    2d4: 00939863  bne          x7, x9, 0x000002e4  # target 0x000002e4
    2d8: 00857663  bgeu         x10, x8, 0x000002e4  # target 0x000002e4
loc_2dc:
    2dc: 00048393  addi         x7, x9, 0
    2e0: 00050413  addi         x8, x10, 0
loc_2e4:
    2e4: 00168693  addi         x13, x13, 1
    2e8: fa1ff06f  jal          x0, 0x00000288  # target 0x00000288
loc_2ec:
    2ec: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    2f0: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    2f4: 00072683  lw           x13, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
    2f8: 00168693  addi         x13, x13, 1
    2fc: 01069693  slli         x13, x13, 16
    300: 0106d693  srli         x13, x13, 16
    304: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    308: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    30c: 00d72023  sw           x13, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    310: ffb49737  lui          x14, 0xffb49  # x14 = 0xffb49000
    314: 02070713  addi         x14, x14, 32  # x14 = 0xffb49020
    318: 00d72023  sw           x13, 0(x14)  # 0xffb49020; write runtime value
    31c: 0ff0000f  fence        0xf, 0xf
    320: ffb018b7  lui          x17, 0xffb01  # x17 = 0xffb01000
    324: 88088893  addi         x17, x17, -1920  # x17 = 0xffb00880 · riscv_local_mem + 0x880
    328: 0008a683  lw           x13, 0(x17)  # riscv_local_mem + 0x880 · 0xffb00880
    32c: 00001737  lui          x14, 0x00001  # x14 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    330: 00e686b3  add          x13, x13, x14
    334: 000117b7  lui          x15, 0x00011  # x15 = 0x00011000
    338: fc078793  addi         x15, x15, -64  # x15 = 0x00010fc0
    33c: 00f6e663  bltu         x13, x15, 0x00000348  # target 0x00000348
    340: 00001837  lui          x16, 0x00001  # x16 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    344: 410686b3  sub          x13, x13, x16
loc_348:
    348: ffb018b7  lui          x17, 0xffb01  # x17 = 0xffb01000
    34c: 88088893  addi         x17, x17, -1920  # x17 = 0xffb00880 · riscv_local_mem + 0x880
    350: 00d8a023  sw           x13, 0(x17)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    354: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    358: fc068693  addi         x13, x13, -64  # x13 = 0x00011fc0
    35c: 0076a023  sw           x7, 0(x13)  # 0x00011fc0; write runtime value
    360: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    364: fc468693  addi         x13, x13, -60  # x13 = 0x00011fc4
    368: 0086a023  sw           x8, 0(x13)  # 0x00011fc4; write runtime value
    36c: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    370: fc868693  addi         x13, x13, -56  # x13 = 0x00011fc8
    374: 00100713  addi         x14, x0, 1  # x14 = 0x00000001
    378: 00e6a023  sw           x14, 0(x13)  # 0x00011fc8; write 0x00000001
    37c: 01000713  addi         x14, x0, 16  # x14 = 0x00000010
    380: 02e306b3  mul          x13, x6, x14
    384: 0000f7b7  lui          x15, 0x0000f  # x15 = 0x0000f000
    388: a4078793  addi         x15, x15, -1472  # x15 = 0x0000ea40
    38c: 00f686b3  add          x13, x13, x15
    390: 410000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x00000394
    394: 428000ef  jal          x1, 0x000007bc  # target 0x000007bc; x1 = 0x00000398
    398: 00012fb7  lui          x31, 0x00012  # x31 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    39c: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00011fc0
    3a0: 00068f13  addi         x30, x13, 0
    3a4: 08100e93  addi         x29, x0, 129  # x29 = 0x00000081
loc_3a8:
    3a8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3ac: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    3b0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    3b4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    3b8: 015a6463  bltu         x20, x21, 0x000003c0  # target 0x000003c0
    3bc: fedff06f  jal          x0, 0x000003a8  # target 0x000003a8
loc_3c0:
    3c0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3c4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    3c8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    3cc: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    3d0: 015a6463  bltu         x20, x21, 0x000003d8  # target 0x000003d8
    3d4: fedff06f  jal          x0, 0x000003c0  # target 0x000003c0
loc_3d8:
    3d8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3dc: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    3e0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    3e4: 014a1a13  slli         x20, x20, 20
    3e8: 014a5a13  srli         x20, x20, 20
    3ec: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_3f0:
    3f0: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    3f4: 000b0463  beq          x22, x0, 0x000003fc  # target 0x000003fc
    3f8: ff9ff06f  jal          x0, 0x000003f0  # target 0x000003f0
loc_3fc:
    3fc: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    400: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00011fc0
    404: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    408: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    40c: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    410: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    414: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write 0x00000081
    418: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    41c: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    420: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    424: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    428: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    42c: 00c00c13  addi         x24, x0, 12  # x24 = 0x0000000c
    430: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x0000000c
    434: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    438: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    43c: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    440: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    444: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    448: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    44c: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_450:
    450: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    454: 000b0463  beq          x22, x0, 0x0000045c  # target 0x0000045c
    458: ff9ff06f  jal          x0, 0x00000450  # target 0x00000450
loc_45c:
    45c: 344000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x00000460
    460: 35c000ef  jal          x1, 0x000007bc  # target 0x000007bc; x1 = 0x00000464
    464: 32031c63  bne          x6, x0, 0x0000079c  # target 0x0000079c
    468: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    46c: 00000413  addi         x8, x0, 0  # x8 = 0x00000000
    470: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    474: 05800713  addi         x14, x0, 88  # x14 = 0x00000058
loc_478:
    478: 04e6f463  bgeu         x13, x14, 0x000004c0  # target 0x000004c0
    47c: 01000813  addi         x16, x0, 16  # x16 = 0x00000010
    480: 030687b3  mul          x15, x13, x16
    484: 0000fa37  lui          x20, 0x0000f  # x20 = 0x0000f000
    488: a40a0a13  addi         x20, x20, -1472  # x20 = 0x0000ea40
    48c: 014787b3  add          x15, x15, x20
loc_490:
    490: 0087a883  lw           x17, 8(x15)  # Address depends on runtime register values
    494: 00089663  bne          x17, x0, 0x000004a0  # target 0x000004a0
    498: 0ff0000f  fence        0xf, 0xf
    49c: ff5ff06f  jal          x0, 0x00000490  # target 0x00000490
loc_4a0:
    4a0: 0007a903  lw           x18, 0(x15)  # Address depends on runtime register values
    4a4: 0047a983  lw           x19, 4(x15)  # Address depends on runtime register values
    4a8: 0007a423  sw           x0, 8(x15)  # Address depends on runtime register values
    4ac: 0123f663  bgeu         x7, x18, 0x000004b8  # target 0x000004b8
    4b0: 00090393  addi         x7, x18, 0
    4b4: 00098413  addi         x8, x19, 0
loc_4b8:
    4b8: 00168693  addi         x13, x13, 1
    4bc: fbdff06f  jal          x0, 0x00000478  # target 0x00000478
loc_4c0:
    4c0: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    4c4: fc068693  addi         x13, x13, -64  # x13 = 0x00011fc0
    4c8: 0086a023  sw           x8, 0(x13)  # 0x00011fc0; write runtime value
    4cc: 78400813  addi         x16, x0, 1924  # x16 = 0x00000784
    4d0: 00082683  lw           x13, 0(x16)  # param argmax_host_address; 0x00000784
    4d4: 78800813  addi         x16, x0, 1928  # x16 = 0x00000788
    4d8: 00082703  lw           x14, 0(x16)  # param write_pos; 0x00000788
    4dc: 00471793  slli         x15, x14, 4
    4e0: 00f686b3  add          x13, x13, x15
    4e4: 2bc000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x000004e8
    4e8: 2d4000ef  jal          x1, 0x000007bc  # target 0x000007bc; x1 = 0x000004ec
    4ec: 00012fb7  lui          x31, 0x00012  # x31 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    4f0: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00011fc0
    4f4: 00068f13  addi         x30, x13, 0
    4f8: 01000eb7  lui          x29, 0x01000  # x29 = 0x01000000
    4fc: 613e8e93  addi         x29, x29, 1555  # x29 = 0x01000613 · CQConfig.PCIE_COORD
loc_500:
    500: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    504: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    508: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    50c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    510: 015a6463  bltu         x20, x21, 0x00000518  # target 0x00000518
    514: fedff06f  jal          x0, 0x00000500  # target 0x00000500
loc_518:
    518: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    51c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    520: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    524: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    528: 015a6463  bltu         x20, x21, 0x00000530  # target 0x00000530
    52c: fedff06f  jal          x0, 0x00000518  # target 0x00000518
loc_530:
    530: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    534: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    538: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    53c: 014a1a13  slli         x20, x20, 20
    540: 014a5a13  srli         x20, x20, 20
    544: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_548:
    548: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    54c: 000b0463  beq          x22, x0, 0x00000554  # target 0x00000554
    550: ff9ff06f  jal          x0, 0x00000548  # target 0x00000548
loc_554:
    554: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    558: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00011fc0
    55c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    560: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    564: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    568: 10000c37  lui          x24, 0x10000  # x24 = 0x10000000 · CQConfig.PCIE_MID
    56c: 018ba823  sw           x24, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x10000000
    570: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write 0x01000613
    574: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    578: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    57c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    580: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    584: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    588: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    58c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000010
    590: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    594: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    598: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    59c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    5a0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    5a4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    5a8: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_5ac:
    5ac: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5b0: 000b0463  beq          x22, x0, 0x000005b8  # target 0x000005b8
    5b4: ff9ff06f  jal          x0, 0x000005ac  # target 0x000005ac
loc_5b8:
    5b8: 1e8000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x000005bc
    5bc: 200000ef  jal          x1, 0x000007bc  # target 0x000007bc; x1 = 0x000005c0
    5c0: 78c00893  addi         x17, x0, 1932  # x17 = 0x0000078c
    5c4: 0008a803  lw           x16, 0(x17)  # param write_token; 0x0000078c
    5c8: 1c080a63  beq          x16, x0, 0x0000079c  # target 0x0000079c
    5cc: 78800893  addi         x17, x0, 1928  # x17 = 0x00000788
    5d0: 0008a683  lw           x13, 0(x17)  # param write_pos; 0x00000788
    5d4: 00a6d713  srli         x14, x13, 10
    5d8: 3ff6f793  andi         x15, x13, 1023
    5dc: 00070f93  addi         x31, x14, 0
    5e0: 2ec000ef  jal          x1, 0x000008cc  # target 0x000008cc; x1 = 0x000005e4
    5e4: 000a8893  addi         x17, x21, 0
    5e8: 000b0913  addi         x18, x22, 0
    5ec: 1b4000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x000005f0
    5f0: 1cc000ef  jal          x1, 0x000007bc  # target 0x000007bc; x1 = 0x000005f4
    5f4: 00088f93  addi         x31, x17, 0
    5f8: 00090f13  addi         x30, x18, 0
    5fc: 00011eb7  lui          x29, 0x00011  # x29 = 0x00011000
    600: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00010fc0
loc_604:
    604: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    608: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    60c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    610: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    614: 015a6463  bltu         x20, x21, 0x0000061c  # target 0x0000061c
    618: fedff06f  jal          x0, 0x00000604  # target 0x00000604
loc_61c:
    61c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    620: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    624: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    628: 014a1a13  slli         x20, x20, 20
    62c: 014a5a13  srli         x20, x20, 20
    630: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_634:
    634: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    638: 000b0463  beq          x22, x0, 0x00000640  # target 0x00000640
    63c: ff9ff06f  jal          x0, 0x00000634  # target 0x00000634
loc_640:
    640: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    644: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    648: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    64c: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    650: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write 0x00010fc0
    654: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    658: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    65c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    660: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    664: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    668: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    66c: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    670: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    674: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
    678: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    67c: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    680: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    684: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    688: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    68c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    690: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_694:
    694: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    698: 000b0463  beq          x22, x0, 0x000006a0  # target 0x000006a0
    69c: ff9ff06f  jal          x0, 0x00000694  # target 0x00000694
loc_6a0:
    6a0: 11c000ef  jal          x1, 0x000007bc  # target 0x000007bc; x1 = 0x000006a4
    6a4: 00279793  slli         x15, x15, 2
    6a8: 000118b7  lui          x17, 0x00011  # x17 = 0x00011000
    6ac: fc088893  addi         x17, x17, -64  # x17 = 0x00010fc0
    6b0: 011787b3  add          x15, x15, x17
    6b4: 0087a023  sw           x8, 0(x15)  # Address depends on runtime register values
    6b8: 00070f93  addi         x31, x14, 0
    6bc: 210000ef  jal          x1, 0x000008cc  # target 0x000008cc; x1 = 0x000006c0
    6c0: 000a8893  addi         x17, x21, 0
    6c4: 000b0913  addi         x18, x22, 0
    6c8: 0d8000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x000006cc
    6cc: 0f0000ef  jal          x1, 0x000007bc  # target 0x000007bc; x1 = 0x000006d0
    6d0: 00011fb7  lui          x31, 0x00011  # x31 = 0x00011000
    6d4: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00010fc0
    6d8: 00088f13  addi         x30, x17, 0
    6dc: 00090e93  addi         x29, x18, 0
loc_6e0:
    6e0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    6e4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    6e8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    6ec: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    6f0: 015a6463  bltu         x20, x21, 0x000006f8  # target 0x000006f8
    6f4: fedff06f  jal          x0, 0x000006e0  # target 0x000006e0
loc_6f8:
    6f8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    6fc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    700: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    704: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    708: 015a6463  bltu         x20, x21, 0x00000710  # target 0x00000710
    70c: fedff06f  jal          x0, 0x000006f8  # target 0x000006f8
loc_710:
    710: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    714: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    718: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    71c: 014a1a13  slli         x20, x20, 20
    720: 014a5a13  srli         x20, x20, 20
    724: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_728:
    728: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    72c: 000b0463  beq          x22, x0, 0x00000734  # target 0x00000734
    730: ff9ff06f  jal          x0, 0x00000728  # target 0x00000728
loc_734:
    734: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    738: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00010fc0
    73c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    740: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    744: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    748: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    74c: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    750: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    754: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    758: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    75c: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    760: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    764: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    768: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
    76c: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    770: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    774: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    778: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    77c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    780: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    784: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_788:
    788: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    78c: 000b0463  beq          x22, x0, 0x00000794  # target 0x00000794
    790: ff9ff06f  jal          x0, 0x00000788  # target 0x00000788
loc_794:
    794: 00c000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x00000798
    798: 024000ef  jal          x1, 0x000007bc  # target 0x000007bc; x1 = 0x0000079c
loc_79c:
    79c: 17c0006f  jal          x0, 0x00000918  # target 0x00000918
loc_7a0:
    7a0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    7a4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    7a8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    7ac: 000a0463  beq          x20, x0, 0x000007b4  # target 0x000007b4
    7b0: ff1ff06f  jal          x0, 0x000007a0  # target 0x000007a0
loc_7b4:
    7b4: 0ff0000f  fence        0xf, 0xf
    7b8: 00008067  jalr         x0, 0(x1)
loc_7bc:
    7bc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    7c0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    7c4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    7c8: 000a0463  beq          x20, x0, 0x000007d0  # target 0x000007d0
    7cc: ff1ff06f  jal          x0, 0x000007bc  # target 0x000007bc
loc_7d0:
    7d0: 0ff0000f  fence        0xf, 0xf
    7d4: 00008067  jalr         x0, 0(x1)
loc_7d8:
    7d8: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    7dc: a00a8a93  addi         x21, x21, -1536  # x21 = 0x0000ea00
    7e0: 000aaa03  lw           x20, 0(x21)  # param e2e_logits; 0x0000ea00
    7e4: 007a7d13  andi         x26, x20, 7
    7e8: ff8a7a13  andi         x20, x20, -8
    7ec: 01af8ab3  add          x21, x31, x26
    7f0: 007afb93  andi         x23, x21, 7
    7f4: 003ada93  srli         x21, x21, 3
    7f8: 00ba9a93  slli         x21, x21, 11
    7fc: 014a8ab3  add          x21, x21, x20
    800: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000800
    804: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000818
    808: 001b9b93  slli         x23, x23, 1
    80c: 017b0b33  add          x22, x22, x23
    810: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    814: 00008067  jalr         x0, 0(x1)
    818: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    81c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    820: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    824: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_828:
    828: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    82c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    830: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    834: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    838: 015a6463  bltu         x20, x21, 0x00000840  # target 0x00000840
    83c: fedff06f  jal          x0, 0x00000828  # target 0x00000828
loc_840:
    840: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    844: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    848: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    84c: 014a1a13  slli         x20, x20, 20
    850: 014a5a13  srli         x20, x20, 20
    854: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_858:
    858: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    85c: 000b0463  beq          x22, x0, 0x00000864  # target 0x00000864
    860: ff9ff06f  jal          x0, 0x00000858  # target 0x00000858
loc_864:
    864: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    868: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    86c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    870: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    874: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    878: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    87c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    880: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    884: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    888: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    88c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    890: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    894: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    898: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    89c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    8a0: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    8a4: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    8a8: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    8ac: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    8b0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    8b4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    8b8: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_8bc:
    8bc: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    8c0: 000b0463  beq          x22, x0, 0x000008c8  # target 0x000008c8
    8c4: ff9ff06f  jal          x0, 0x000008bc  # target 0x000008bc
loc_8c8:
    8c8: 00008067  jalr         x0, 0(x1)
loc_8cc:
    8cc: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    8d0: 000aaa03  lw           x20, 0(x21)  # param e2e_token_history; 0x00000780
    8d4: 007a7d13  andi         x26, x20, 7
    8d8: ff8a7a13  andi         x20, x20, -8
    8dc: 01af8ab3  add          x21, x31, x26
    8e0: 007afb93  andi         x23, x21, 7
    8e4: 003ada93  srli         x21, x21, 3
    8e8: 00ca9a93  slli         x21, x21, 12
    8ec: 014a8ab3  add          x21, x21, x20
    8f0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000008f0
    8f4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000908
    8f8: 001b9b93  slli         x23, x23, 1
    8fc: 017b0b33  add          x22, x22, x23
    900: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    904: 00008067  jalr         x0, 0(x1)
    908: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    90c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    910: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    914: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    918:           j FW_BRISC+4   # return to firmware, linked at install
