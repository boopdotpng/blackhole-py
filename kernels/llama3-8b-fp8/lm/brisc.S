# llama3 8b-fp8 decode: lm, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_lm_weight, 0x788=e2e_final_norm, 0x78c=e2e_lm_weight_rows, 0xe9c0=e2e_logits, 0xe9c4=e2e_lm_weight_row_start, 0xe9c8=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000172b7  lui          x5, 0x00017  # x5 = 0x00017000
      c: 08028293  addi         x5, x5, 128  # x5 = 0x00017080
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00017080
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     24: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     28: 0000f537  lui          x10, 0x0000f  # x10 = 0x0000f000
     2c: 08050513  addi         x10, x10, 128  # x10 = 0x0000f080
     30: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x0000f080
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
     64: 00800393  addi         x7, x0, 8  # x7 = 0x00000008
     68: 406383b3  sub          x7, x7, x6
     6c: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
     70: 0083f663  bgeu         x7, x8, 0x0000007c  # target 0x0000007c
     74: 0ff0000f  fence        0xf, 0xf
     78: fd5ff06f  jal          x0, 0x0000004c  # target 0x0000004c
loc_7c:
     7c: 0ff0000f  fence        0xf, 0xf
     80: 2c0000ef  jal          x1, 0x00000340  # target 0x00000340; x1 = 0x00000084
     84: 2d8000ef  jal          x1, 0x0000035c  # target 0x0000035c; x1 = 0x00000088
     88: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     8c: 2ec000ef  jal          x1, 0x00000378  # target 0x00000378; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 00017eb7  lui          x29, 0x00017  # x29 = 0x00017000
     a4: 080e8e93  addi         x29, x29, 128  # x29 = 0x00017080
     a8: 354000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x000000ac
     ac: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     b0: 2c8000ef  jal          x1, 0x00000378  # target 0x00000378; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
     c8: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00017880
     cc: 330000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x000000d0
     d0: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     d4: 2a4000ef  jal          x1, 0x00000378  # target 0x00000378; x1 = 0x000000d8
     d8: 000a8213  addi         x4, x21, 0
     dc: 000b0293  addi         x5, x22, 0
     e0: 00020f93  addi         x31, x4, 0
     e4: 00028f13  addi         x30, x5, 0
     e8: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
     ec: 080e8e93  addi         x29, x29, 128  # x29 = 0x00018080
     f0: 30c000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x000000f4
     f4: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     f8: 280000ef  jal          x1, 0x00000378  # target 0x00000378; x1 = 0x000000fc
     fc: 000a8213  addi         x4, x21, 0
    100: 000b0293  addi         x5, x22, 0
    104: 00020f93  addi         x31, x4, 0
    108: 00028f13  addi         x30, x5, 0
    10c: 00019eb7  lui          x29, 0x00019  # x29 = 0x00019000
    110: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00018880
    114: 2e8000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x00000118
    118: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    11c: 384000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x00000120
    120: 000a8213  addi         x4, x21, 0
    124: 000b0293  addi         x5, x22, 0
    128: 00020f93  addi         x31, x4, 0
    12c: 00028f13  addi         x30, x5, 0
    130: 00019eb7  lui          x29, 0x00019  # x29 = 0x00019000
    134: 080e8e93  addi         x29, x29, 128  # x29 = 0x00019080
    138: 2c4000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x0000013c
    13c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    140: 360000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x00000144
    144: 000a8213  addi         x4, x21, 0
    148: 000b0293  addi         x5, x22, 0
    14c: 00020f93  addi         x31, x4, 0
    150: 00028f13  addi         x30, x5, 0
    154: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
    158: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00019880
    15c: 2a0000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x00000160
    160: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    164: 33c000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x00000168
    168: 000a8213  addi         x4, x21, 0
    16c: 000b0293  addi         x5, x22, 0
    170: 00020f93  addi         x31, x4, 0
    174: 00028f13  addi         x30, x5, 0
    178: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
    17c: 080e8e93  addi         x29, x29, 128  # x29 = 0x0001a080
    180: 27c000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x00000184
    184: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    188: 318000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x0000018c
    18c: 000a8213  addi         x4, x21, 0
    190: 000b0293  addi         x5, x22, 0
    194: 00020f93  addi         x31, x4, 0
    198: 00028f13  addi         x30, x5, 0
    19c: 0001beb7  lui          x29, 0x0001b  # x29 = 0x0001b000
    1a0: 880e8e93  addi         x29, x29, -1920  # x29 = 0x0001a880
    1a4: 258000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x000001a8
    1a8: 1b4000ef  jal          x1, 0x0000035c  # target 0x0000035c; x1 = 0x000001ac
    1ac: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1b0: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1b4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    1b8: 000042b7  lui          x5, 0x00004  # x5 = 0x00004000
    1bc: 00520233  add          x4, x4, x5
    1c0: 0001b337  lui          x6, 0x0001b  # x6 = 0x0001b000
    1c4: 08030313  addi         x6, x6, 128  # x6 = 0x0001b080
    1c8: 00626663  bltu         x4, x6, 0x000001d4  # target 0x000001d4
    1cc: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    1d0: 40720233  sub          x4, x4, x7
loc_1d4:
    1d4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1d8: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1dc: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1e0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1e4: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1e8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    1ec: 00820213  addi         x4, x4, 8
    1f0: 01021213  slli         x4, x4, 16
    1f4: 01025213  srli         x4, x4, 16
    1f8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1fc: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    200: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    204: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    208: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    20c: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    210: 0ff0000f  fence        0xf, 0xf
    214: 78c00293  addi         x5, x0, 1932  # x5 = 0x0000078c
    218: 0002a203  lw           x4, 0(x5)  # param e2e_lm_weight_rows; 0x0000078c
    21c: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    220: 0003a283  lw           x5, 0(x7)  # param e2e_lm_weight; 0x00000784
    224: ff82f293  andi         x5, x5, -8
    228: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    22c: 9c448493  addi         x9, x9, -1596  # x9 = 0x0000e9c4
    230: 0004a383  lw           x7, 0(x9)  # param e2e_lm_weight_row_start; 0x0000e9c4
    234: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    238: 028383b3  mul          x7, x7, x8
    23c: 0073f313  andi         x6, x7, 7
    240: 0033d393  srli         x7, x7, 3
    244: 00b39393  slli         x7, x7, 11
    248: 007282b3  add          x5, x5, x7
    24c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    250: 00020413  addi         x8, x4, 0
loc_254:
    254: 0e83f463  bgeu         x7, x8, 0x0000033c  # target 0x0000033c
    258: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    25c: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    260: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_264:
    264: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    268: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    26c: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    270: 40a485b3  sub          x11, x9, x10
    274: 01059593  slli         x11, x11, 16
    278: 0105d593  srli         x11, x11, 16
    27c: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    280: 40b60633  sub          x12, x12, x11
    284: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    288: 00d67663  bgeu         x12, x13, 0x00000294  # target 0x00000294
    28c: 0ff0000f  fence        0xf, 0xf
    290: fd5ff06f  jal          x0, 0x00000264  # target 0x00000264
loc_294:
    294: 0ff0000f  fence        0xf, 0xf
    298: 0a8000ef  jal          x1, 0x00000340  # target 0x00000340; x1 = 0x0000029c
    29c: 0c0000ef  jal          x1, 0x0000035c  # target 0x0000035c; x1 = 0x000002a0
    2a0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2a4: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    2a8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    2ac: 00028f93  addi         x31, x5, 0
    2b0: 00030f13  addi         x30, x6, 0
    2b4: 00048e93  addi         x29, x9, 0
    2b8: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    2bc: 268000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x000002c0
    2c0: 000f8293  addi         x5, x31, 0
    2c4: 000f0313  addi         x6, x30, 0
    2c8: 094000ef  jal          x1, 0x0000035c  # target 0x0000035c; x1 = 0x000002cc
    2cc: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2d0: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2d4: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    2d8: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    2dc: 00a484b3  add          x9, x9, x10
    2e0: 000135b7  lui          x11, 0x00013  # x11 = 0x00013000
    2e4: 08058593  addi         x11, x11, 128  # x11 = 0x00013080
    2e8: 00b4e663  bltu         x9, x11, 0x000002f4  # target 0x000002f4
    2ec: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    2f0: 40c484b3  sub          x9, x9, x12
loc_2f4:
    2f4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2f8: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2fc: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    300: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    304: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    308: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    30c: 00448493  addi         x9, x9, 4
    310: 01049493  slli         x9, x9, 16
    314: 0104d493  srli         x9, x9, 16
    318: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    31c: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    320: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    324: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    328: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    32c: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    330: 0ff0000f  fence        0xf, 0xf
    334: 00138393  addi         x7, x7, 1
    338: f1dff06f  jal          x0, 0x00000254  # target 0x00000254
loc_33c:
    33c: 3100006f  jal          x0, 0x0000064c  # target 0x0000064c
loc_340:
    340: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    344: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    348: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    34c: 000a0463  beq          x20, x0, 0x00000354  # target 0x00000354
    350: ff1ff06f  jal          x0, 0x00000340  # target 0x00000340
loc_354:
    354: 0ff0000f  fence        0xf, 0xf
    358: 00008067  jalr         x0, 0(x1)
loc_35c:
    35c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    360: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    364: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    368: 000a0463  beq          x20, x0, 0x00000370  # target 0x00000370
    36c: ff1ff06f  jal          x0, 0x0000035c  # target 0x0000035c
loc_370:
    370: 0ff0000f  fence        0xf, 0xf
    374: 00008067  jalr         x0, 0(x1)
loc_378:
    378: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    37c: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x00000780
    380: 007a7d13  andi         x26, x20, 7
    384: ff8a7a13  andi         x20, x20, -8
    388: 01af8ab3  add          x21, x31, x26
    38c: 007afb93  andi         x23, x21, 7
    390: 003ada93  srli         x21, x21, 3
    394: 00ba9a93  slli         x21, x21, 11
    398: 014a8ab3  add          x21, x21, x20
    39c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000039c
    3a0: 030b0b13  addi         x22, x22, 48  # x22 = 0x000003cc
    3a4: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    3a8: 9c8e8e93  addi         x29, x29, -1592  # x29 = 0x0000e9c8
    3ac: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e9c8
    3b0: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    3b4: 03cd8db3  mul          x27, x27, x28
    3b8: 01bb0b33  add          x22, x22, x27
    3bc: 001b9b93  slli         x23, x23, 1
    3c0: 017b0b33  add          x22, x22, x23
    3c4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    3c8: 00008067  jalr         x0, 0(x1)
    3cc: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3d0: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3d4: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    3d8: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    3dc: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3e0: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3e4: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    3e8: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    3ec: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    3f0: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3f4: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    3f8: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_3fc:
    3fc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    400: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    404: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    408: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    40c: 015a6463  bltu         x20, x21, 0x00000414  # target 0x00000414
    410: fedff06f  jal          x0, 0x000003fc  # target 0x000003fc
loc_414:
    414: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    418: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    41c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    420: 014a1a13  slli         x20, x20, 20
    424: 014a5a13  srli         x20, x20, 20
    428: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_42c:
    42c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    430: 000b0463  beq          x22, x0, 0x00000438  # target 0x00000438
    434: ff9ff06f  jal          x0, 0x0000042c  # target 0x0000042c
loc_438:
    438: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    43c: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    440: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    444: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    448: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    44c: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    450: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    454: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    458: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    45c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    460: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    464: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    468: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    46c: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    470: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    474: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    478: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    47c: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    480: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    484: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    488: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    48c: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_490:
    490: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    494: 000b0463  beq          x22, x0, 0x0000049c  # target 0x0000049c
    498: ff9ff06f  jal          x0, 0x00000490  # target 0x00000490
loc_49c:
    49c: 00008067  jalr         x0, 0(x1)
loc_4a0:
    4a0: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    4a4: 000aaa03  lw           x20, 0(x21)  # param e2e_final_norm; 0x00000788
    4a8: 007a7d13  andi         x26, x20, 7
    4ac: ff8a7a13  andi         x20, x20, -8
    4b0: 01af8ab3  add          x21, x31, x26
    4b4: 007afb93  andi         x23, x21, 7
    4b8: 003ada93  srli         x21, x21, 3
    4bc: 00ba9a93  slli         x21, x21, 11
    4c0: 014a8ab3  add          x21, x21, x20
    4c4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004c4
    4c8: 030b0b13  addi         x22, x22, 48  # x22 = 0x000004f4
    4cc: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    4d0: 9c8e8e93  addi         x29, x29, -1592  # x29 = 0x0000e9c8
    4d4: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e9c8
    4d8: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    4dc: 03cd8db3  mul          x27, x27, x28
    4e0: 01bb0b33  add          x22, x22, x27
    4e4: 001b9b93  slli         x23, x23, 1
    4e8: 017b0b33  add          x22, x22, x23
    4ec: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4f0: 00008067  jalr         x0, 0(x1)
    4f4: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f8: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4fc: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    500: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    504: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    508: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    50c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    510: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    514: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    518: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    51c: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    520: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_524:
    524: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000524
    528: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x0000061c
    52c: 0000fcb7  lui          x25, 0x0000f  # x25 = 0x0000f000
    530: 9c8c8c93  addi         x25, x25, -1592  # x25 = 0x0000e9c8
    534: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0000e9c8
    538: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    53c: 038b8bb3  mul          x23, x23, x24
    540: 017a0a33  add          x20, x20, x23
loc_544:
    544: 001f1a93  slli         x21, x30, 1
    548: 014a8ab3  add          x21, x21, x20
    54c: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_550:
    550: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    554: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    558: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    55c: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    560: 018be463  bltu         x23, x24, 0x00000568  # target 0x00000568
    564: fedff06f  jal          x0, 0x00000550  # target 0x00000550
loc_568:
    568: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    56c: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    570: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    574: 014b9b93  slli         x23, x23, 20
    578: 014bdb93  srli         x23, x23, 20
    57c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_580:
    580: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    584: 000c8463  beq          x25, x0, 0x0000058c  # target 0x0000058c
    588: ff9ff06f  jal          x0, 0x00000580  # target 0x00000580
loc_58c:
    58c: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    590: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    594: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    598: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    59c: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    5a0: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    5a4: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    5a8: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    5ac: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    5b0: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    5b4: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    5b8: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    5bc: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5c0: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    5c4: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    5c8: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    5cc: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    5d0: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    5d4: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    5d8: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    5dc: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    5e0: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_5e4:
    5e4: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    5e8: 000c8463  beq          x25, x0, 0x000005f0  # target 0x000005f0
    5ec: ff9ff06f  jal          x0, 0x000005e4  # target 0x000005e4
loc_5f0:
    5f0: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5f4: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    5f8: 016e8eb3  add          x29, x29, x22
    5fc: 001f0f13  addi         x30, x30, 1
    600: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    604: 015f1663  bne          x30, x21, 0x00000610  # target 0x00000610
    608: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    60c: 016f8fb3  add          x31, x31, x22
loc_610:
    610: fffe0e13  addi         x28, x28, -1
    614: f20e18e3  bne          x28, x0, 0x00000544  # target 0x00000544
    618: 00008067  jalr         x0, 0(x1)
    61c: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    620: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    624: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    628: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    62c: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    630: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    634: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    638: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    63c: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    640: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    644: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    648: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    64c:           j FW_BRISC+4   # return to firmware, linked at install
