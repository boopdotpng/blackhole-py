# llama3 8b-fp8 decode: lm, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x7c0=e2e_x_a_decode_token, 0x7c4=e2e_lm_weight, 0x7c8=e2e_final_norm, 0x7cc=e2e_lm_weight_rows, 0x8180=e2e_logits, 0x8184=e2e_lm_weight_row_start, 0x8188=dram_port
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000982b7  lui          x5, 0x00098  # x5 = 0x00098000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00098000
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
     5c: 00800393  addi         x7, x0, 8  # x7 = 0x00000008
     60: 406383b3  sub          x7, x7, x6
     64: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
     68: 0083f663  bgeu         x7, x8, 0x00000074  # target 0x00000074
     6c: 0ff0000f  fence        0xf, 0xf
     70: fd5ff06f  jal          x0, 0x00000044  # target 0x00000044
loc_74:
     74: 0ff0000f  fence        0xf, 0xf
     78: 2a8000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x0000007c
     7c: 2c0000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x00000080
     80: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     84: 2d4000ef  jal          x1, 0x00000358  # target 0x00000358; x1 = 0x00000088
     88: 000a8213  addi         x4, x21, 0
     8c: 000b0293  addi         x5, x22, 0
     90: 00020f93  addi         x31, x4, 0
     94: 00028f13  addi         x30, x5, 0
     98: 00098eb7  lui          x29, 0x00098  # x29 = 0x00098000
     9c: 340000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x000000a0
     a0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     a4: 2b4000ef  jal          x1, 0x00000358  # target 0x00000358; x1 = 0x000000a8
     a8: 000a8213  addi         x4, x21, 0
     ac: 000b0293  addi         x5, x22, 0
     b0: 00020f93  addi         x31, x4, 0
     b4: 00028f13  addi         x30, x5, 0
     b8: 00099eb7  lui          x29, 0x00099  # x29 = 0x00099000
     bc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00098800
     c0: 31c000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x000000c4
     c4: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     c8: 290000ef  jal          x1, 0x00000358  # target 0x00000358; x1 = 0x000000cc
     cc: 000a8213  addi         x4, x21, 0
     d0: 000b0293  addi         x5, x22, 0
     d4: 00020f93  addi         x31, x4, 0
     d8: 00028f13  addi         x30, x5, 0
     dc: 00099eb7  lui          x29, 0x00099  # x29 = 0x00099000
     e0: 2fc000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x000000e4
     e4: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     e8: 270000ef  jal          x1, 0x00000358  # target 0x00000358; x1 = 0x000000ec
     ec: 000a8213  addi         x4, x21, 0
     f0: 000b0293  addi         x5, x22, 0
     f4: 00020f93  addi         x31, x4, 0
     f8: 00028f13  addi         x30, x5, 0
     fc: 0009aeb7  lui          x29, 0x0009a  # x29 = 0x0009a000
    100: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00099800
    104: 2d8000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x00000108
    108: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    10c: 374000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000110
    110: 000a8213  addi         x4, x21, 0
    114: 000b0293  addi         x5, x22, 0
    118: 00020f93  addi         x31, x4, 0
    11c: 00028f13  addi         x30, x5, 0
    120: 0009aeb7  lui          x29, 0x0009a  # x29 = 0x0009a000
    124: 2b8000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x00000128
    128: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    12c: 354000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000130
    130: 000a8213  addi         x4, x21, 0
    134: 000b0293  addi         x5, x22, 0
    138: 00020f93  addi         x31, x4, 0
    13c: 00028f13  addi         x30, x5, 0
    140: 0009beb7  lui          x29, 0x0009b  # x29 = 0x0009b000
    144: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009a800
    148: 294000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x0000014c
    14c: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    150: 330000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000154
    154: 000a8213  addi         x4, x21, 0
    158: 000b0293  addi         x5, x22, 0
    15c: 00020f93  addi         x31, x4, 0
    160: 00028f13  addi         x30, x5, 0
    164: 0009beb7  lui          x29, 0x0009b  # x29 = 0x0009b000
    168: 274000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x0000016c
    16c: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    170: 310000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000174
    174: 000a8213  addi         x4, x21, 0
    178: 000b0293  addi         x5, x22, 0
    17c: 00020f93  addi         x31, x4, 0
    180: 00028f13  addi         x30, x5, 0
    184: 0009ceb7  lui          x29, 0x0009c  # x29 = 0x0009c000
    188: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009b800
    18c: 250000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x00000190
    190: 1ac000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x00000194
    194: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    198: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    19c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    1a0: 000042b7  lui          x5, 0x00004  # x5 = 0x00004000
    1a4: 00520233  add          x4, x4, x5
    1a8: 0009c337  lui          x6, 0x0009c  # x6 = 0x0009c000
    1ac: 00626663  bltu         x4, x6, 0x000001b8  # target 0x000001b8
    1b0: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    1b4: 40720233  sub          x4, x4, x7
loc_1b8:
    1b8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1bc: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1c0: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1c4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1c8: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1cc: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    1d0: 00820213  addi         x4, x4, 8
    1d4: 01021213  slli         x4, x4, 16
    1d8: 01025213  srli         x4, x4, 16
    1dc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1e0: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1e4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1e8: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    1ec: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    1f0: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    1f4: 0ff0000f  fence        0xf, 0xf
    1f8: 7cc00293  addi         x5, x0, 1996  # x5 = 0x000007cc
    1fc: 0002a203  lw           x4, 0(x5)  # param e2e_lm_weight_rows; 0x000007cc
    200: 7c400393  addi         x7, x0, 1988  # x7 = 0x000007c4
    204: 0003a283  lw           x5, 0(x7)  # param e2e_lm_weight; 0x000007c4
    208: ff82f293  andi         x5, x5, -8
    20c: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    210: 18448493  addi         x9, x9, 388  # x9 = 0x00008184
    214: 0004a383  lw           x7, 0(x9)  # param e2e_lm_weight_row_start; 0x00008184
    218: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    21c: 028383b3  mul          x7, x7, x8
    220: 0073f313  andi         x6, x7, 7
    224: 0033d393  srli         x7, x7, 3
    228: 00b39393  slli         x7, x7, 11
    22c: 007282b3  add          x5, x5, x7
    230: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    234: 00020413  addi         x8, x4, 0
loc_238:
    238: 0e83f263  bgeu         x7, x8, 0x0000031c  # target 0x0000031c
    23c: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    240: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    244: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_248:
    248: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    24c: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    250: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    254: 40a485b3  sub          x11, x9, x10
    258: 01059593  slli         x11, x11, 16
    25c: 0105d593  srli         x11, x11, 16
    260: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    264: 40b60633  sub          x12, x12, x11
    268: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    26c: 00d67663  bgeu         x12, x13, 0x00000278  # target 0x00000278
    270: 0ff0000f  fence        0xf, 0xf
    274: fd5ff06f  jal          x0, 0x00000248  # target 0x00000248
loc_278:
    278: 0ff0000f  fence        0xf, 0xf
    27c: 0a4000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000280
    280: 0bc000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x00000284
    284: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    288: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    28c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    290: 00028f93  addi         x31, x5, 0
    294: 00030f13  addi         x30, x6, 0
    298: 00048e93  addi         x29, x9, 0
    29c: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    2a0: 264000ef  jal          x1, 0x00000504  # target 0x00000504; x1 = 0x000002a4
    2a4: 000f8293  addi         x5, x31, 0
    2a8: 000f0313  addi         x6, x30, 0
    2ac: 090000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x000002b0
    2b0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2b4: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2b8: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    2bc: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    2c0: 00a484b3  add          x9, x9, x10
    2c4: 000945b7  lui          x11, 0x00094  # x11 = 0x00094000
    2c8: 00b4e663  bltu         x9, x11, 0x000002d4  # target 0x000002d4
    2cc: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    2d0: 40c484b3  sub          x9, x9, x12
loc_2d4:
    2d4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2d8: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2dc: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    2e0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2e4: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    2e8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    2ec: 00448493  addi         x9, x9, 4
    2f0: 01049493  slli         x9, x9, 16
    2f4: 0104d493  srli         x9, x9, 16
    2f8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2fc: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    300: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    304: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    308: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    30c: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    310: 0ff0000f  fence        0xf, 0xf
    314: 00138393  addi         x7, x7, 1
    318: f21ff06f  jal          x0, 0x00000238  # target 0x00000238
loc_31c:
    31c: 3100006f  jal          x0, 0x0000062c  # target 0x0000062c
loc_320:
    320: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    324: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    328: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    32c: 000a0463  beq          x20, x0, 0x00000334  # target 0x00000334
    330: ff1ff06f  jal          x0, 0x00000320  # target 0x00000320
loc_334:
    334: 0ff0000f  fence        0xf, 0xf
    338: 00008067  jalr         x0, 0(x1)
loc_33c:
    33c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    340: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    344: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    348: 000a0463  beq          x20, x0, 0x00000350  # target 0x00000350
    34c: ff1ff06f  jal          x0, 0x0000033c  # target 0x0000033c
loc_350:
    350: 0ff0000f  fence        0xf, 0xf
    354: 00008067  jalr         x0, 0(x1)
loc_358:
    358: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    35c: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x000007c0
    360: 007a7d13  andi         x26, x20, 7
    364: ff8a7a13  andi         x20, x20, -8
    368: 01af8ab3  add          x21, x31, x26
    36c: 007afb93  andi         x23, x21, 7
    370: 003ada93  srli         x21, x21, 3
    374: 00ba9a93  slli         x21, x21, 11
    378: 014a8ab3  add          x21, x21, x20
    37c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000037c
    380: 030b0b13  addi         x22, x22, 48  # x22 = 0x000003ac
    384: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    388: 188e8e93  addi         x29, x29, 392  # x29 = 0x00008188
    38c: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00008188
    390: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    394: 03cd8db3  mul          x27, x27, x28
    398: 01bb0b33  add          x22, x22, x27
    39c: 001b9b93  slli         x23, x23, 1
    3a0: 017b0b33  add          x22, x22, x23
    3a4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    3a8: 00008067  jalr         x0, 0(x1)
    3ac: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3b0: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3b4: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    3b8: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    3bc: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3c0: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3c4: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    3c8: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    3cc: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    3d0: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3d4: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    3d8: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_3dc:
    3dc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3e0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    3e4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    3e8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    3ec: 015a6463  bltu         x20, x21, 0x000003f4  # target 0x000003f4
    3f0: fedff06f  jal          x0, 0x000003dc  # target 0x000003dc
loc_3f4:
    3f4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3f8: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    3fc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    400: 014a1a13  slli         x20, x20, 20
    404: 014a5a13  srli         x20, x20, 20
    408: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_40c:
    40c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    410: 000b0463  beq          x22, x0, 0x00000418  # target 0x00000418
    414: ff9ff06f  jal          x0, 0x0000040c  # target 0x0000040c
loc_418:
    418: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    41c: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    420: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    424: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    428: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    42c: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    430: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    434: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    438: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    43c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    440: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    444: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    448: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    44c: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    450: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    454: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    458: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    45c: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    460: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    464: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    468: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    46c: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_470:
    470: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    474: 000b0463  beq          x22, x0, 0x0000047c  # target 0x0000047c
    478: ff9ff06f  jal          x0, 0x00000470  # target 0x00000470
loc_47c:
    47c: 00008067  jalr         x0, 0(x1)
loc_480:
    480: 7c800a93  addi         x21, x0, 1992  # x21 = 0x000007c8
    484: 000aaa03  lw           x20, 0(x21)  # param e2e_final_norm; 0x000007c8
    488: 007a7d13  andi         x26, x20, 7
    48c: ff8a7a13  andi         x20, x20, -8
    490: 01af8ab3  add          x21, x31, x26
    494: 007afb93  andi         x23, x21, 7
    498: 003ada93  srli         x21, x21, 3
    49c: 00ba9a93  slli         x21, x21, 11
    4a0: 014a8ab3  add          x21, x21, x20
    4a4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004a4
    4a8: 030b0b13  addi         x22, x22, 48  # x22 = 0x000004d4
    4ac: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    4b0: 188e8e93  addi         x29, x29, 392  # x29 = 0x00008188
    4b4: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00008188
    4b8: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    4bc: 03cd8db3  mul          x27, x27, x28
    4c0: 01bb0b33  add          x22, x22, x27
    4c4: 001b9b93  slli         x23, x23, 1
    4c8: 017b0b33  add          x22, x22, x23
    4cc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4d0: 00008067  jalr         x0, 0(x1)
    4d4: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4d8: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4dc: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4e0: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    4e4: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4e8: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4ec: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    4f0: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    4f4: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    4f8: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4fc: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    500: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_504:
    504: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000504
    508: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x000005fc
    50c: 00008cb7  lui          x25, 0x00008  # x25 = 0x00008000
    510: 188c8c93  addi         x25, x25, 392  # x25 = 0x00008188
    514: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x00008188
    518: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    51c: 038b8bb3  mul          x23, x23, x24
    520: 017a0a33  add          x20, x20, x23
loc_524:
    524: 001f1a93  slli         x21, x30, 1
    528: 014a8ab3  add          x21, x21, x20
    52c: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_530:
    530: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    534: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    538: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    53c: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    540: 018be463  bltu         x23, x24, 0x00000548  # target 0x00000548
    544: fedff06f  jal          x0, 0x00000530  # target 0x00000530
loc_548:
    548: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    54c: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    550: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    554: 014b9b93  slli         x23, x23, 20
    558: 014bdb93  srli         x23, x23, 20
    55c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_560:
    560: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    564: 000c8463  beq          x25, x0, 0x0000056c  # target 0x0000056c
    568: ff9ff06f  jal          x0, 0x00000560  # target 0x00000560
loc_56c:
    56c: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    570: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    574: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    578: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    57c: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    580: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    584: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    588: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    58c: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    590: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    594: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    598: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    59c: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5a0: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    5a4: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    5a8: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    5ac: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    5b0: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    5b4: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    5b8: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    5bc: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    5c0: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_5c4:
    5c4: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    5c8: 000c8463  beq          x25, x0, 0x000005d0  # target 0x000005d0
    5cc: ff9ff06f  jal          x0, 0x000005c4  # target 0x000005c4
loc_5d0:
    5d0: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5d4: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    5d8: 016e8eb3  add          x29, x29, x22
    5dc: 001f0f13  addi         x30, x30, 1
    5e0: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    5e4: 015f1663  bne          x30, x21, 0x000005f0  # target 0x000005f0
    5e8: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    5ec: 016f8fb3  add          x31, x31, x22
loc_5f0:
    5f0: fffe0e13  addi         x28, x28, -1
    5f4: f20e18e3  bne          x28, x0, 0x00000524  # target 0x00000524
    5f8: 00008067  jalr         x0, 0(x1)
    5fc: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    600: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    604: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    608: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    60c: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    610: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    614: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    618: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    61c: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    620: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    624: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    628: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    62c:           j FW_BRISC+4   # return to firmware, linked at install
