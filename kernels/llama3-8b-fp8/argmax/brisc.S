# llama3 8b-fp8 decode: argmax, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x7c0=e2e_token_history, 0x7c4=argmax_host_address, 0x7c8=argmax_count, 0x7cc=write_pos, 0x7d0=write_token, 0x81c0=e2e_logits, 0x81c4=argmax_start, 0x81c8=argmax_core
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000902b7  lui          x5, 0x00090  # x5 = 0x00090000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00090000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     20: 88038393  addi         x7, x7, -1920  # x7 = 0xffb00880 · riscv_local_mem + 0x880
     24: 00091437  lui          x8, 0x00091  # x8 = 0x00091000
     28: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00091000
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
     78: 17d000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x0000007c
     7c: 195000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x00000080
     80: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     84: 1a9000ef  jal          x1, 0x00000a2c  # target 0x00000a2c; x1 = 0x00000088
     88: 000a8213  addi         x4, x21, 0
     8c: 000b0293  addi         x5, x22, 0
     90: 00020f93  addi         x31, x4, 0
     94: 00028f13  addi         x30, x5, 0
     98: 00090eb7  lui          x29, 0x00090  # x29 = 0x00090000
     9c: 1e1000ef  jal          x1, 0x00000a7c  # target 0x00000a7c; x1 = 0x000000a0
     a0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     a4: 189000ef  jal          x1, 0x00000a2c  # target 0x00000a2c; x1 = 0x000000a8
     a8: 000a8213  addi         x4, x21, 0
     ac: 000b0293  addi         x5, x22, 0
     b0: 00020f93  addi         x31, x4, 0
     b4: 00028f13  addi         x30, x5, 0
     b8: 00091eb7  lui          x29, 0x00091  # x29 = 0x00091000
     bc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00090800
     c0: 1bd000ef  jal          x1, 0x00000a7c  # target 0x00000a7c; x1 = 0x000000c4
     c4: 14d000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x000000c8
     c8: 7c800393  addi         x7, x0, 1992  # x7 = 0x000007c8
     cc: 0003a203  lw           x4, 0(x7)  # param argmax_count; 0x000007c8
     d0: 000083b7  lui          x7, 0x00008  # x7 = 0x00008000
     d4: 1c438393  addi         x7, x7, 452  # x7 = 0x000081c4
     d8: 0003a283  lw           x5, 0(x7)  # param argmax_start; 0x000081c4
     dc: 000083b7  lui          x7, 0x00008  # x7 = 0x00008000
     e0: 1c838393  addi         x7, x7, 456  # x7 = 0x000081c8
     e4: 0003a303  lw           x6, 0(x7)  # param argmax_core; 0x000081c8
     e8: 53800393  addi         x7, x0, 1336  # x7 = 0x00000538
     ec: 04721e63  bne          x4, x7, 0x00000148  # target 0x00000148
     f0: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
     f4: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
     f8: 00091437  lui          x8, 0x00091  # x8 = 0x00091000
     fc: 94040413  addi         x8, x8, -1728  # x8 = 0x00090940
    100: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    104: 03000593  addi         x11, x0, 48  # x11 = 0x00000030
loc_108:
    108: 00b57a63  bgeu         x10, x11, 0x0000011c  # target 0x0000011c
    10c: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    110: 00440413  addi         x8, x8, 4
    114: 00150513  addi         x10, x10, 1
    118: ff1ff06f  jal          x0, 0x00000108  # target 0x00000108
loc_11c:
    11c: ff8104b7  lui          x9, 0xff810  # x9 = 0xff810000
    120: f8048493  addi         x9, x9, -128  # x9 = 0xff80ff80
    124: 00091437  lui          x8, 0x00091  # x8 = 0x00091000
    128: b3040413  addi         x8, x8, -1232  # x8 = 0x00090b30
    12c: 00000513  addi         x10, x0, 0  # x10 = 0x00000000
    130: 13400593  addi         x11, x0, 308  # x11 = 0x00000134
loc_134:
    134: 00b57a63  bgeu         x10, x11, 0x00000148  # target 0x00000148
    138: 00942023  sw           x9, 0(x8)  # Address depends on runtime register values
    13c: 00440413  addi         x8, x8, 4
    140: 00150513  addi         x10, x10, 1
    144: ff1ff06f  jal          x0, 0x00000134  # target 0x00000134
loc_148:
    148: 0ff0000f  fence        0xf, 0xf
    14c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    150: 87858593  addi         x11, x11, -1928  # x11 = 0xffb00878 · riscv_local_mem + 0x878
    154: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x878 · 0xffb00878
    158: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    15c: 008383b3  add          x7, x7, x8
    160: 000914b7  lui          x9, 0x00091  # x9 = 0x00091000
    164: 0093e663  bltu         x7, x9, 0x00000170  # target 0x00000170
    168: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    16c: 40a383b3  sub          x7, x7, x10
loc_170:
    170: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    174: 87858593  addi         x11, x11, -1928  # x11 = 0xffb00878 · riscv_local_mem + 0x878
    178: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    17c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    180: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    184: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    188: 00238393  addi         x7, x7, 2
    18c: 01039393  slli         x7, x7, 16
    190: 0103d393  srli         x7, x7, 16
    194: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    198: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    19c: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1a0: ffb48437  lui          x8, 0xffb48  # x8 = 0xffb48000
    1a4: 02840413  addi         x8, x8, 40  # x8 = 0xffb48028
    1a8: 00742023  sw           x7, 0(x8)  # 0xffb48028; write runtime value
    1ac: 0ff0000f  fence        0xf, 0xf
    1b0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1b4: 88458593  addi         x11, x11, -1916  # x11 = 0xffb00884 · riscv_local_mem + 0x884
    1b8: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x884 · 0xffb00884
    1bc: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_1c0:
    1c0: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
    1c4: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
    1c8: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
    1cc: 407404b3  sub          x9, x8, x7
    1d0: 01049493  slli         x9, x9, 16
    1d4: 0104d493  srli         x9, x9, 16
    1d8: 00a4f663  bgeu         x9, x10, 0x000001e4  # target 0x000001e4
    1dc: 0ff0000f  fence        0xf, 0xf
    1e0: fe1ff06f  jal          x0, 0x000001c0  # target 0x000001c0
loc_1e4:
    1e4: 0ff0000f  fence        0xf, 0xf
    1e8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1ec: 80000437  lui          x8, 0x80000  # x8 = 0x80000000 · arc_apb + 0x0
    1f0: fff40413  addi         x8, x8, -1  # x8 = 0x7fffffff
    1f4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    1f8: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    1fc: 0006a583  lw           x11, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    200: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    204: 02000713  addi         x14, x0, 32  # x14 = 0x00000020
loc_208:
    208: 06e6f263  bgeu         x13, x14, 0x0000026c  # target 0x0000026c
    20c: 0005a483  lw           x9, 0(x11)  # Address depends on runtime register values
    210: 00f4d493  srli         x9, x9, 15
    214: 0045a603  lw           x12, 4(x11)  # Address depends on runtime register values
    218: c0067513  andi         x10, x12, -1024
    21c: 20067793  andi         x15, x12, 512
    220: 00f56533  or           x10, x10, x15
    224: 10067793  andi         x15, x12, 256
    228: 0047d793  srli         x15, x15, 4
    22c: 00f56533  or           x10, x10, x15
    230: 0f067793  andi         x15, x12, 240
    234: 00179793  slli         x15, x15, 1
    238: 00f56533  or           x10, x10, x15
    23c: 00f67793  andi         x15, x12, 15
    240: 00f56533  or           x10, x10, x15
    244: 00858593  addi         x11, x11, 8
    248: 00457e63  bgeu         x10, x4, 0x00000264  # target 0x00000264
    24c: 00a28533  add          x10, x5, x10
    250: 0093e663  bltu         x7, x9, 0x0000025c  # target 0x0000025c
    254: 00939863  bne          x7, x9, 0x00000264  # target 0x00000264
    258: 00857663  bgeu         x10, x8, 0x00000264  # target 0x00000264
loc_25c:
    25c: 00048393  addi         x7, x9, 0
    260: 00050413  addi         x8, x10, 0
loc_264:
    264: 00168693  addi         x13, x13, 1
    268: fa1ff06f  jal          x0, 0x00000208  # target 0x00000208
loc_26c:
    26c: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    270: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    274: 00072683  lw           x13, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
    278: 00168693  addi         x13, x13, 1
    27c: 01069693  slli         x13, x13, 16
    280: 0106d693  srli         x13, x13, 16
    284: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    288: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    28c: 00d72023  sw           x13, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    290: ffb49737  lui          x14, 0xffb49  # x14 = 0xffb49000
    294: 02070713  addi         x14, x14, 32  # x14 = 0xffb49020
    298: 00d72023  sw           x13, 0(x14)  # 0xffb49020; write runtime value
    29c: 0ff0000f  fence        0xf, 0xf
    2a0: ffb018b7  lui          x17, 0xffb01  # x17 = 0xffb01000
    2a4: 88088893  addi         x17, x17, -1920  # x17 = 0xffb00880 · riscv_local_mem + 0x880
    2a8: 0008a683  lw           x13, 0(x17)  # riscv_local_mem + 0x880 · 0xffb00880
    2ac: 00001737  lui          x14, 0x00001  # x14 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2b0: 00e686b3  add          x13, x13, x14
    2b4: 000927b7  lui          x15, 0x00092  # x15 = 0x00092000
    2b8: 00f6e663  bltu         x13, x15, 0x000002c4  # target 0x000002c4
    2bc: 00001837  lui          x16, 0x00001  # x16 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2c0: 410686b3  sub          x13, x13, x16
loc_2c4:
    2c4: ffb018b7  lui          x17, 0xffb01  # x17 = 0xffb01000
    2c8: 88088893  addi         x17, x17, -1920  # x17 = 0xffb00880 · riscv_local_mem + 0x880
    2cc: 00d8a023  sw           x13, 0(x17)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    2d0: 000936b7  lui          x13, 0x00093  # x13 = 0x00093000
    2d4: 0076a023  sw           x7, 0(x13)  # 0x00093000; write runtime value
    2d8: 000936b7  lui          x13, 0x00093  # x13 = 0x00093000
    2dc: 00468693  addi         x13, x13, 4  # x13 = 0x00093004
    2e0: 0086a023  sw           x8, 0(x13)  # 0x00093004; write runtime value
    2e4: 000936b7  lui          x13, 0x00093  # x13 = 0x00093000
    2e8: 00868693  addi         x13, x13, 8  # x13 = 0x00093008
    2ec: 00100713  addi         x14, x0, 1  # x14 = 0x00000001
    2f0: 00e6a023  sw           x14, 0(x13)  # 0x00093008; write 0x00000001
    2f4: 01000713  addi         x14, x0, 16  # x14 = 0x00000010
    2f8: 02e306b3  mul          x13, x6, x14
    2fc: 000097b7  lui          x15, 0x00009  # x15 = 0x00009000
    300: 80078793  addi         x15, x15, -2048  # x15 = 0x00008800
    304: 00f686b3  add          x13, x13, x15
    308: 6ec000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x0000030c
    30c: 704000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x00000310
    310: 00093fb7  lui          x31, 0x00093  # x31 = 0x00093000
    314: 00068f13  addi         x30, x13, 0
    318: 08100e93  addi         x29, x0, 129  # x29 = 0x00000081
loc_31c:
    31c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    320: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    324: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    328: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    32c: 015a6463  bltu         x20, x21, 0x00000334  # target 0x00000334
    330: fedff06f  jal          x0, 0x0000031c  # target 0x0000031c
loc_334:
    334: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    338: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    33c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    340: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    344: 015a6463  bltu         x20, x21, 0x0000034c  # target 0x0000034c
    348: fedff06f  jal          x0, 0x00000334  # target 0x00000334
loc_34c:
    34c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    350: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    354: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    358: 014a1a13  slli         x20, x20, 20
    35c: 014a5a13  srli         x20, x20, 20
    360: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_364:
    364: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    368: 000b0463  beq          x22, x0, 0x00000370  # target 0x00000370
    36c: ff9ff06f  jal          x0, 0x00000364  # target 0x00000364
loc_370:
    370: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    374: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00093000
    378: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    37c: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    380: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    384: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    388: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write 0x00000081
    38c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    390: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    394: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    398: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    39c: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    3a0: 00c00c13  addi         x24, x0, 12  # x24 = 0x0000000c
    3a4: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x0000000c
    3a8: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    3ac: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    3b0: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    3b4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    3b8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    3bc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    3c0: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_3c4:
    3c4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    3c8: 000b0463  beq          x22, x0, 0x000003d0  # target 0x000003d0
    3cc: ff9ff06f  jal          x0, 0x000003c4  # target 0x000003c4
loc_3d0:
    3d0: 624000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x000003d4
    3d4: 63c000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x000003d8
    3d8: 60031c63  bne          x6, x0, 0x000009f0  # target 0x000009f0
    3dc: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    3e0: 00000413  addi         x8, x0, 0  # x8 = 0x00000000
    3e4: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    3e8: 06000713  addi         x14, x0, 96  # x14 = 0x00000060
loc_3ec:
    3ec: 04e6f463  bgeu         x13, x14, 0x00000434  # target 0x00000434
    3f0: 01000813  addi         x16, x0, 16  # x16 = 0x00000010
    3f4: 030687b3  mul          x15, x13, x16
    3f8: 00009a37  lui          x20, 0x00009  # x20 = 0x00009000
    3fc: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00008800
    400: 014787b3  add          x15, x15, x20
loc_404:
    404: 0087a883  lw           x17, 8(x15)  # Address depends on runtime register values
    408: 00089663  bne          x17, x0, 0x00000414  # target 0x00000414
    40c: 0ff0000f  fence        0xf, 0xf
    410: ff5ff06f  jal          x0, 0x00000404  # target 0x00000404
loc_414:
    414: 0007a903  lw           x18, 0(x15)  # Address depends on runtime register values
    418: 0047a983  lw           x19, 4(x15)  # Address depends on runtime register values
    41c: 0007a423  sw           x0, 8(x15)  # Address depends on runtime register values
    420: 0123f663  bgeu         x7, x18, 0x0000042c  # target 0x0000042c
    424: 00090393  addi         x7, x18, 0
    428: 00098413  addi         x8, x19, 0
loc_42c:
    42c: 00168693  addi         x13, x13, 1
    430: fbdff06f  jal          x0, 0x000003ec  # target 0x000003ec
loc_434:
    434: 000936b7  lui          x13, 0x00093  # x13 = 0x00093000
    438: 0086a023  sw           x8, 0(x13)  # 0x00093000; write runtime value
    43c: 7c400813  addi         x16, x0, 1988  # x16 = 0x000007c4
    440: 00082683  lw           x13, 0(x16)  # param argmax_host_address; 0x000007c4
    444: 7cc00813  addi         x16, x0, 1996  # x16 = 0x000007cc
    448: 00082703  lw           x14, 0(x16)  # param write_pos; 0x000007cc
    44c: 00471793  slli         x15, x14, 4
    450: 00f686b3  add          x13, x13, x15
    454: 5a0000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x00000458
    458: 5b8000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x0000045c
    45c: 00093fb7  lui          x31, 0x00093  # x31 = 0x00093000
    460: 00068f13  addi         x30, x13, 0
    464: 01000eb7  lui          x29, 0x01000  # x29 = 0x01000000
    468: 613e8e93  addi         x29, x29, 1555  # x29 = 0x01000613 · CQConfig.PCIE_COORD
loc_46c:
    46c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    470: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    474: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    478: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    47c: 015a6463  bltu         x20, x21, 0x00000484  # target 0x00000484
    480: fedff06f  jal          x0, 0x0000046c  # target 0x0000046c
loc_484:
    484: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    488: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    48c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    490: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    494: 015a6463  bltu         x20, x21, 0x0000049c  # target 0x0000049c
    498: fedff06f  jal          x0, 0x00000484  # target 0x00000484
loc_49c:
    49c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4a0: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    4a4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    4a8: 014a1a13  slli         x20, x20, 20
    4ac: 014a5a13  srli         x20, x20, 20
    4b0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_4b4:
    4b4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    4b8: 000b0463  beq          x22, x0, 0x000004c0  # target 0x000004c0
    4bc: ff9ff06f  jal          x0, 0x000004b4  # target 0x000004b4
loc_4c0:
    4c0: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    4c4: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00093000
    4c8: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    4cc: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    4d0: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    4d4: 10000c37  lui          x24, 0x10000  # x24 = 0x10000000 · CQConfig.PCIE_MID
    4d8: 018ba823  sw           x24, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x10000000
    4dc: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write 0x01000613
    4e0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    4e4: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    4e8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    4ec: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    4f0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    4f4: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    4f8: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000010
    4fc: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    500: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    504: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    508: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    50c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    510: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    514: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_518:
    518: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    51c: 000b0463  beq          x22, x0, 0x00000524  # target 0x00000524
    520: ff9ff06f  jal          x0, 0x00000518  # target 0x00000518
loc_524:
    524: 4d0000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x00000528
    528: 4e8000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x0000052c
    52c: 7d000893  addi         x17, x0, 2000  # x17 = 0x000007d0
    530: 0008a803  lw           x16, 0(x17)  # param write_token; 0x000007d0
    534: 1c080463  beq          x16, x0, 0x000006fc  # target 0x000006fc
    538: 7cc00893  addi         x17, x0, 1996  # x17 = 0x000007cc
    53c: 0008a683  lw           x13, 0(x17)  # param write_pos; 0x000007cc
    540: 00a6d713  srli         x14, x13, 10
    544: 3ff6f793  andi         x15, x13, 1023
    548: 00070f93  addi         x31, x14, 0
    54c: 5d4000ef  jal          x1, 0x00000b20  # target 0x00000b20; x1 = 0x00000550
    550: 000a8893  addi         x17, x21, 0
    554: 000b0913  addi         x18, x22, 0
    558: 49c000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x0000055c
    55c: 4b4000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x00000560
    560: 00088f93  addi         x31, x17, 0
    564: 00090f13  addi         x30, x18, 0
    568: 00092eb7  lui          x29, 0x00092  # x29 = 0x00092000
loc_56c:
    56c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    570: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    574: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    578: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    57c: 015a6463  bltu         x20, x21, 0x00000584  # target 0x00000584
    580: fedff06f  jal          x0, 0x0000056c  # target 0x0000056c
loc_584:
    584: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    588: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    58c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    590: 014a1a13  slli         x20, x20, 20
    594: 014a5a13  srli         x20, x20, 20
    598: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_59c:
    59c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5a0: 000b0463  beq          x22, x0, 0x000005a8  # target 0x000005a8
    5a4: ff9ff06f  jal          x0, 0x0000059c  # target 0x0000059c
loc_5a8:
    5a8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    5ac: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    5b0: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    5b4: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    5b8: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write 0x00092000
    5bc: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    5c0: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    5c4: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    5c8: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    5cc: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    5d0: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    5d4: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    5d8: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5dc: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
    5e0: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    5e4: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    5e8: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    5ec: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    5f0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    5f4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    5f8: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_5fc:
    5fc: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    600: 000b0463  beq          x22, x0, 0x00000608  # target 0x00000608
    604: ff9ff06f  jal          x0, 0x000005fc  # target 0x000005fc
loc_608:
    608: 408000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x0000060c
    60c: 00279793  slli         x15, x15, 2
    610: 000928b7  lui          x17, 0x00092  # x17 = 0x00092000
    614: 011787b3  add          x15, x15, x17
    618: 0087a023  sw           x8, 0(x15)  # Address depends on runtime register values
    61c: 00070f93  addi         x31, x14, 0
    620: 500000ef  jal          x1, 0x00000b20  # target 0x00000b20; x1 = 0x00000624
    624: 000a8893  addi         x17, x21, 0
    628: 000b0913  addi         x18, x22, 0
    62c: 3c8000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x00000630
    630: 3e0000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x00000634
    634: 00092fb7  lui          x31, 0x00092  # x31 = 0x00092000
    638: 00088f13  addi         x30, x17, 0
    63c: 00090e93  addi         x29, x18, 0
loc_640:
    640: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    644: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    648: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    64c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    650: 015a6463  bltu         x20, x21, 0x00000658  # target 0x00000658
    654: fedff06f  jal          x0, 0x00000640  # target 0x00000640
loc_658:
    658: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    65c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    660: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    664: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    668: 015a6463  bltu         x20, x21, 0x00000670  # target 0x00000670
    66c: fedff06f  jal          x0, 0x00000658  # target 0x00000658
loc_670:
    670: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    674: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    678: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    67c: 014a1a13  slli         x20, x20, 20
    680: 014a5a13  srli         x20, x20, 20
    684: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_688:
    688: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    68c: 000b0463  beq          x22, x0, 0x00000694  # target 0x00000694
    690: ff9ff06f  jal          x0, 0x00000688  # target 0x00000688
loc_694:
    694: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    698: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write 0x00092000
    69c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    6a0: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    6a4: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    6a8: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    6ac: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    6b0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    6b4: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    6b8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    6bc: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    6c0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    6c4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6c8: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
    6cc: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    6d0: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    6d4: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    6d8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    6dc: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    6e0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    6e4: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_6e8:
    6e8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    6ec: 000b0463  beq          x22, x0, 0x000006f4  # target 0x000006f4
    6f0: ff9ff06f  jal          x0, 0x000006e8  # target 0x000006e8
loc_6f4:
    6f4: 300000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x000006f8
    6f8: 318000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x000006fc
loc_6fc:
    6fc: 7cc00793  addi         x15, x0, 1996  # x15 = 0x000007cc
    700: 0007a683  lw           x13, 0(x15)  # param write_pos; 0x000007cc
    704: 000937b7  lui          x15, 0x00093  # x15 = 0x00093000
    708: 01078793  addi         x15, x15, 16  # x15 = 0x00093010
    70c: 00d7a023  sw           x13, 0(x15)  # 0x00093010; write runtime value
    710: 001807b7  lui          x15, 0x00180  # x15 = 0x00180000 · TensixL1.SIZE
    714: fe078793  addi         x15, x15, -32  # x15 = 0x0017ffe0 · TensixL1.RUNTIME_PARAM_BASE · TensixL1.DATA_BUFFER_SPACE_END
    718: 00d7a023  sw           x13, 0(x15)  # TensixL1.RUNTIME_PARAM_BASE · TensixL1.DATA_BUFFER_SPACE_END · 0x0017ffe0; write runtime value
    71c: 00168713  addi         x14, x13, 1
    720: 000937b7  lui          x15, 0x00093  # x15 = 0x00093000
    724: 01478793  addi         x15, x15, 20  # x15 = 0x00093014
    728: 00e7a023  sw           x14, 0(x15)  # 0x00093014; write runtime value
    72c: 001807b7  lui          x15, 0x00180  # x15 = 0x00180000 · TensixL1.SIZE
    730: fe478793  addi         x15, x15, -28  # x15 = 0x0017ffe4
    734: 00e7a023  sw           x14, 0(x15)  # 0x0017ffe4; write runtime value
    738: 000937b7  lui          x15, 0x00093  # x15 = 0x00093000
    73c: 01878793  addi         x15, x15, 24  # x15 = 0x00093018
    740: 00100813  addi         x16, x0, 1  # x16 = 0x00000001
    744: 0107a023  sw           x16, 0(x15)  # 0x00093018; write 0x00000001
    748: 001807b7  lui          x15, 0x00180  # x15 = 0x00180000 · TensixL1.SIZE
    74c: fe878793  addi         x15, x15, -24  # x15 = 0x0017ffe8
    750: 00100813  addi         x16, x0, 1  # x16 = 0x00000001
    754: 0107a023  sw           x16, 0(x15)  # 0x0017ffe8; write 0x00000001
    758: 000937b7  lui          x15, 0x00093  # x15 = 0x00093000
    75c: 01c78793  addi         x15, x15, 28  # x15 = 0x0009301c
    760: 00d7a023  sw           x13, 0(x15)  # 0x0009301c; write runtime value
    764: 001807b7  lui          x15, 0x00180  # x15 = 0x00180000 · TensixL1.SIZE
    768: fec78793  addi         x15, x15, -20  # x15 = 0x0017ffec
    76c: 00d7a023  sw           x13, 0(x15)  # 0x0017ffec; write runtime value
    770: 0056d713  srli         x14, x13, 5
    774: 00170713  addi         x14, x14, 1
    778: 000937b7  lui          x15, 0x00093  # x15 = 0x00093000
    77c: 02078793  addi         x15, x15, 32  # x15 = 0x00093020
    780: 00e7a023  sw           x14, 0(x15)  # 0x00093020; write runtime value
    784: 001807b7  lui          x15, 0x00180  # x15 = 0x00180000 · TensixL1.SIZE
    788: ff078793  addi         x15, x15, -16  # x15 = 0x0017fff0
    78c: 00e7a023  sw           x14, 0(x15)  # 0x0017fff0; write runtime value
    790: 01f6f713  andi         x14, x13, 31
    794: 00170713  addi         x14, x14, 1
    798: 000937b7  lui          x15, 0x00093  # x15 = 0x00093000
    79c: 02478793  addi         x15, x15, 36  # x15 = 0x00093024
    7a0: 00e7a023  sw           x14, 0(x15)  # 0x00093024; write runtime value
    7a4: 001807b7  lui          x15, 0x00180  # x15 = 0x00180000 · TensixL1.SIZE
    7a8: ff478793  addi         x15, x15, -12  # x15 = 0x0017fff4
    7ac: 00e7a023  sw           x14, 0(x15)  # 0x0017fff4; write runtime value
    7b0: 244000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x000007b4
    7b4: 25c000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x000007b8
    7b8: 00093fb7  lui          x31, 0x00093  # x31 = 0x00093000
    7bc: 010f8f93  addi         x31, x31, 16  # x31 = 0x00093010
    7c0: 00180f37  lui          x30, 0x00180  # x30 = 0x00180000 · TensixL1.SIZE
    7c4: fe0f0f13  addi         x30, x30, -32  # x30 = 0x0017ffe0 · TensixL1.RUNTIME_PARAM_BASE · TensixL1.DATA_BUFFER_SPACE_END
loc_7c8:
    7c8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    7cc: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    7d0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    7d4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    7d8: 015a6463  bltu         x20, x21, 0x000007e0  # target 0x000007e0
    7dc: fedff06f  jal          x0, 0x000007c8  # target 0x000007c8
loc_7e0:
    7e0: ffb20b37  lui          x22, 0xffb20  # x22 = 0xffb20000 · noc0_regs + 0x0
    7e4: 148b0b13  addi         x22, x22, 328  # x22 = 0xffb20148 · noc0_regs + 0x148
    7e8: 000b2a03  lw           x20, 0(x22)  # noc0_regs + 0x148 · 0xffb20148
    7ec: 014a1a13  slli         x20, x20, 20
    7f0: 014a5a13  srli         x20, x20, 20
    7f4: 0008aab7  lui          x21, 0x0008a  # x21 = 0x0008a000
    7f8: 1cca8a93  addi         x21, x21, 460  # x21 = 0x0008a1cc
    7fc: ffb20b37  lui          x22, 0xffb20  # x22 = 0xffb20000 · noc0_regs + 0x0
loc_800:
    800: 040b2b83  lw           x23, 64(x22)  # noc0_regs + 0x40 · 0xffb20040
    804: 000b8463  beq          x23, x0, 0x0000080c  # target 0x0000080c
    808: ff9ff06f  jal          x0, 0x00000800  # target 0x00000800
loc_80c:
    80c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    810: 01fc2023  sw           x31, 0(x24)  # noc0_regs + 0x0 · 0xffb20000; write 0x00093010
    814: 000c2223  sw           x0, 4(x24)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    818: 014c2423  sw           x20, 8(x24)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    81c: 01ec2623  sw           x30, 12(x24)  # noc0_regs + 0xc · 0xffb2000c; write 0x0017ffe0
    820: 000c2823  sw           x0, 16(x24)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    824: 015c2a23  sw           x21, 20(x24)  # noc0_regs + 0x14 · 0xffb20014; write 0x0008a1cc
    828: 40000c93  addi         x25, x0, 1024  # x25 = 0x00000400
    82c: 019c2c23  sw           x25, 24(x24)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    830: 00008cb7  lui          x25, 0x00008  # x25 = 0x00008000
    834: 0a2c8c93  addi         x25, x25, 162  # x25 = 0x000080a2
    838: 019c2e23  sw           x25, 28(x24)  # noc0_regs + 0x1c · 0xffb2001c; write 0x000080a2
    83c: 01800c93  addi         x25, x0, 24  # x25 = 0x00000018
    840: 039c2023  sw           x25, 32(x24)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000018
    844: 020c2223  sw           x0, 36(x24)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    848: 020c2423  sw           x0, 40(x24)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    84c: 020c2623  sw           x0, 44(x24)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    850: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    854: 040c0c13  addi         x24, x24, 64  # x24 = 0xffb20040 · noc0_regs + 0x40
    858: 00100c93  addi         x25, x0, 1  # x25 = 0x00000001
    85c: 019c2023  sw           x25, 0(x24)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_860:
    860: 040b2b83  lw           x23, 64(x22)  # noc0_regs + 0x40 · 0xffb20040
    864: 000b8463  beq          x23, x0, 0x0000086c  # target 0x0000086c
    868: ff9ff06f  jal          x0, 0x00000860  # target 0x00000860
loc_86c:
    86c: 188000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x00000870
    870: 184000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x00000874
    874: 19c000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x00000878
    878: 00093fb7  lui          x31, 0x00093  # x31 = 0x00093000
    87c: 010f8f93  addi         x31, x31, 16  # x31 = 0x00093010
    880: 00180f37  lui          x30, 0x00180  # x30 = 0x00180000 · TensixL1.SIZE
    884: fe0f0f13  addi         x30, x30, -32  # x30 = 0x0017ffe0 · TensixL1.RUNTIME_PARAM_BASE · TensixL1.DATA_BUFFER_SPACE_END
loc_888:
    888: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    88c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    890: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    894: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    898: 015a6463  bltu         x20, x21, 0x000008a0  # target 0x000008a0
    89c: fedff06f  jal          x0, 0x00000888  # target 0x00000888
loc_8a0:
    8a0: ffb20b37  lui          x22, 0xffb20  # x22 = 0xffb20000 · noc0_regs + 0x0
    8a4: 148b0b13  addi         x22, x22, 328  # x22 = 0xffb20148 · noc0_regs + 0x148
    8a8: 000b2a03  lw           x20, 0(x22)  # noc0_regs + 0x148 · 0xffb20148
    8ac: 014a1a13  slli         x20, x20, 20
    8b0: 014a5a13  srli         x20, x20, 20
    8b4: 00081ab7  lui          x21, 0x00081  # x21 = 0x00081000
    8b8: 2c7a8a93  addi         x21, x21, 711  # x21 = 0x000812c7
    8bc: ffb20b37  lui          x22, 0xffb20  # x22 = 0xffb20000 · noc0_regs + 0x0
loc_8c0:
    8c0: 040b2b83  lw           x23, 64(x22)  # noc0_regs + 0x40 · 0xffb20040
    8c4: 000b8463  beq          x23, x0, 0x000008cc  # target 0x000008cc
    8c8: ff9ff06f  jal          x0, 0x000008c0  # target 0x000008c0
loc_8cc:
    8cc: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    8d0: 01fc2023  sw           x31, 0(x24)  # noc0_regs + 0x0 · 0xffb20000; write 0x00093010
    8d4: 000c2223  sw           x0, 4(x24)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    8d8: 014c2423  sw           x20, 8(x24)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    8dc: 01ec2623  sw           x30, 12(x24)  # noc0_regs + 0xc · 0xffb2000c; write 0x0017ffe0
    8e0: 000c2823  sw           x0, 16(x24)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    8e4: 015c2a23  sw           x21, 20(x24)  # noc0_regs + 0x14 · 0xffb20014; write 0x000812c7
    8e8: 40000c93  addi         x25, x0, 1024  # x25 = 0x00000400
    8ec: 019c2c23  sw           x25, 24(x24)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    8f0: 00008cb7  lui          x25, 0x00008  # x25 = 0x00008000
    8f4: 0a2c8c93  addi         x25, x25, 162  # x25 = 0x000080a2
    8f8: 019c2e23  sw           x25, 28(x24)  # noc0_regs + 0x1c · 0xffb2001c; write 0x000080a2
    8fc: 01800c93  addi         x25, x0, 24  # x25 = 0x00000018
    900: 039c2023  sw           x25, 32(x24)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000018
    904: 020c2223  sw           x0, 36(x24)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    908: 020c2423  sw           x0, 40(x24)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    90c: 020c2623  sw           x0, 44(x24)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    910: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    914: 040c0c13  addi         x24, x24, 64  # x24 = 0xffb20040 · noc0_regs + 0x40
    918: 00100c93  addi         x25, x0, 1  # x25 = 0x00000001
    91c: 019c2023  sw           x25, 0(x24)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_920:
    920: 040b2b83  lw           x23, 64(x22)  # noc0_regs + 0x40 · 0xffb20040
    924: 000b8463  beq          x23, x0, 0x0000092c  # target 0x0000092c
    928: ff9ff06f  jal          x0, 0x00000920  # target 0x00000920
loc_92c:
    92c: 0c8000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x00000930
    930: 0c4000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x00000934
    934: 0dc000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x00000938
    938: 00093fb7  lui          x31, 0x00093  # x31 = 0x00093000
    93c: 010f8f93  addi         x31, x31, 16  # x31 = 0x00093010
    940: 00180f37  lui          x30, 0x00180  # x30 = 0x00180000 · TensixL1.SIZE
    944: fe0f0f13  addi         x30, x30, -32  # x30 = 0x0017ffe0 · TensixL1.RUNTIME_PARAM_BASE · TensixL1.DATA_BUFFER_SPACE_END
loc_948:
    948: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    94c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    950: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    954: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    958: 015a6463  bltu         x20, x21, 0x00000960  # target 0x00000960
    95c: fedff06f  jal          x0, 0x00000948  # target 0x00000948
loc_960:
    960: ffb20b37  lui          x22, 0xffb20  # x22 = 0xffb20000 · noc0_regs + 0x0
    964: 148b0b13  addi         x22, x22, 328  # x22 = 0xffb20148 · noc0_regs + 0x148
    968: 000b2a03  lw           x20, 0(x22)  # noc0_regs + 0x148 · 0xffb20148
    96c: 014a1a13  slli         x20, x20, 20
    970: 014a5a13  srli         x20, x20, 20
    974: 0020aab7  lui          x21, 0x0020a  # x21 = 0x0020a000
    978: 2cba8a93  addi         x21, x21, 715  # x21 = 0x0020a2cb
    97c: ffb20b37  lui          x22, 0xffb20  # x22 = 0xffb20000 · noc0_regs + 0x0
loc_980:
    980: 040b2b83  lw           x23, 64(x22)  # noc0_regs + 0x40 · 0xffb20040
    984: 000b8463  beq          x23, x0, 0x0000098c  # target 0x0000098c
    988: ff9ff06f  jal          x0, 0x00000980  # target 0x00000980
loc_98c:
    98c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    990: 01fc2023  sw           x31, 0(x24)  # noc0_regs + 0x0 · 0xffb20000; write 0x00093010
    994: 000c2223  sw           x0, 4(x24)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    998: 014c2423  sw           x20, 8(x24)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    99c: 01ec2623  sw           x30, 12(x24)  # noc0_regs + 0xc · 0xffb2000c; write 0x0017ffe0
    9a0: 000c2823  sw           x0, 16(x24)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    9a4: 015c2a23  sw           x21, 20(x24)  # noc0_regs + 0x14 · 0xffb20014; write 0x0020a2cb
    9a8: 40000c93  addi         x25, x0, 1024  # x25 = 0x00000400
    9ac: 019c2c23  sw           x25, 24(x24)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    9b0: 00008cb7  lui          x25, 0x00008  # x25 = 0x00008000
    9b4: 0a2c8c93  addi         x25, x25, 162  # x25 = 0x000080a2
    9b8: 019c2e23  sw           x25, 28(x24)  # noc0_regs + 0x1c · 0xffb2001c; write 0x000080a2
    9bc: 01800c93  addi         x25, x0, 24  # x25 = 0x00000018
    9c0: 039c2023  sw           x25, 32(x24)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000018
    9c4: 020c2223  sw           x0, 36(x24)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    9c8: 020c2423  sw           x0, 40(x24)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    9cc: 020c2623  sw           x0, 44(x24)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    9d0: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    9d4: 040c0c13  addi         x24, x24, 64  # x24 = 0xffb20040 · noc0_regs + 0x40
    9d8: 00100c93  addi         x25, x0, 1  # x25 = 0x00000001
    9dc: 019c2023  sw           x25, 0(x24)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_9e0:
    9e0: 040b2b83  lw           x23, 64(x22)  # noc0_regs + 0x40 · 0xffb20040
    9e4: 000b8463  beq          x23, x0, 0x000009ec  # target 0x000009ec
    9e8: ff9ff06f  jal          x0, 0x000009e0  # target 0x000009e0
loc_9ec:
    9ec: 008000ef  jal          x1, 0x000009f4  # target 0x000009f4; x1 = 0x000009f0
loc_9f0:
    9f0: 17c0006f  jal          x0, 0x00000b6c  # target 0x00000b6c
loc_9f4:
    9f4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    9f8: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    9fc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    a00: 000a0463  beq          x20, x0, 0x00000a08  # target 0x00000a08
    a04: ff1ff06f  jal          x0, 0x000009f4  # target 0x000009f4
loc_a08:
    a08: 0ff0000f  fence        0xf, 0xf
    a0c: 00008067  jalr         x0, 0(x1)
loc_a10:
    a10: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    a14: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    a18: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    a1c: 000a0463  beq          x20, x0, 0x00000a24  # target 0x00000a24
    a20: ff1ff06f  jal          x0, 0x00000a10  # target 0x00000a10
loc_a24:
    a24: 0ff0000f  fence        0xf, 0xf
    a28: 00008067  jalr         x0, 0(x1)
loc_a2c:
    a2c: 00008ab7  lui          x21, 0x00008  # x21 = 0x00008000
    a30: 1c0a8a93  addi         x21, x21, 448  # x21 = 0x000081c0
    a34: 000aaa03  lw           x20, 0(x21)  # param e2e_logits; 0x000081c0
    a38: 007a7d13  andi         x26, x20, 7
    a3c: ff8a7a13  andi         x20, x20, -8
    a40: 01af8ab3  add          x21, x31, x26
    a44: 007afb93  andi         x23, x21, 7
    a48: 003ada93  srli         x21, x21, 3
    a4c: 00ba9a93  slli         x21, x21, 11
    a50: 014a8ab3  add          x21, x21, x20
    a54: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000a54
    a58: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000a6c
    a5c: 001b9b93  slli         x23, x23, 1
    a60: 017b0b33  add          x22, x22, x23
    a64: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    a68: 00008067  jalr         x0, 0(x1)
    a6c: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    a70: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    a74: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    a78: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_a7c:
    a7c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    a80: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    a84: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    a88: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    a8c: 015a6463  bltu         x20, x21, 0x00000a94  # target 0x00000a94
    a90: fedff06f  jal          x0, 0x00000a7c  # target 0x00000a7c
loc_a94:
    a94: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    a98: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    a9c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    aa0: 014a1a13  slli         x20, x20, 20
    aa4: 014a5a13  srli         x20, x20, 20
    aa8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_aac:
    aac: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    ab0: 000b0463  beq          x22, x0, 0x00000ab8  # target 0x00000ab8
    ab4: ff9ff06f  jal          x0, 0x00000aac  # target 0x00000aac
loc_ab8:
    ab8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    abc: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    ac0: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    ac4: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    ac8: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    acc: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    ad0: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    ad4: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    ad8: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    adc: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    ae0: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    ae4: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    ae8: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    aec: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    af0: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    af4: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    af8: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    afc: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    b00: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    b04: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    b08: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    b0c: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_b10:
    b10: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    b14: 000b0463  beq          x22, x0, 0x00000b1c  # target 0x00000b1c
    b18: ff9ff06f  jal          x0, 0x00000b10  # target 0x00000b10
loc_b1c:
    b1c: 00008067  jalr         x0, 0(x1)
loc_b20:
    b20: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    b24: 000aaa03  lw           x20, 0(x21)  # param e2e_token_history; 0x000007c0
    b28: 007a7d13  andi         x26, x20, 7
    b2c: ff8a7a13  andi         x20, x20, -8
    b30: 01af8ab3  add          x21, x31, x26
    b34: 007afb93  andi         x23, x21, 7
    b38: 003ada93  srli         x21, x21, 3
    b3c: 00ca9a93  slli         x21, x21, 12
    b40: 014a8ab3  add          x21, x21, x20
    b44: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000b44
    b48: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000b5c
    b4c: 001b9b93  slli         x23, x23, 1
    b50: 017b0b33  add          x22, x22, x23
    b54: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    b58: 00008067  jalr         x0, 0(x1)
    b5c: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    b60: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    b64: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    b68: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    b6c:           j FW_BRISC+4   # return to firmware, linked at install
