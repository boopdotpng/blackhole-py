# llama3 8b-fp8 decode: o, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x7c0=e2e_context_decode_token, 0x7c4=e2e_l0_q, 0x7c8=input_scale_0, 0x7cc=input_scale_1, 0x7d0=output_scale_0_0, 0x7d4=output_scale_0_1, 0x7d8=e2e_x_b, 0x7dc=e2e_x_a, 0x8040=e2e_q_compact, 0x8044=e2e_l0_q_row_start, 0x8048=dense_start, 0x804c=e2e_l0_q_rows, 0x8050=dram_port
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000a32b7  lui          x5, 0x000a3  # x5 = 0x000a3000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x000a2800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x000a2800
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     24: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     28: 00090537  lui          x10, 0x00090  # x10 = 0x00090000
     2c: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00090000
     30: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     34: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
     38: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     3c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     40: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     44: 0004a203  lw           x4, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_48:
     48: ffb4c4b7  lui          x9, 0xffb4c  # x9 = 0xffb4c000
     4c: 02048493  addi         x9, x9, 32  # x9 = 0xffb4c020
     50: 0004d283  lhu          x5, 0(x9)  # 0xffb4c020
     54: 40520333  sub          x6, x4, x5
     58: 01031313  slli         x6, x6, 16
     5c: 01035313  srli         x6, x6, 16
     60: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     64: 406383b3  sub          x7, x7, x6
     68: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
     6c: 0083f663  bgeu         x7, x8, 0x00000078  # target 0x00000078
     70: 0ff0000f  fence        0xf, 0xf
     74: fd5ff06f  jal          x0, 0x00000048  # target 0x00000048
loc_78:
     78: 0ff0000f  fence        0xf, 0xf
     7c: 2b0000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x00000080
     80: 2c8000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x00000084
     84: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     88: 2dc000ef  jal          x1, 0x00000364  # target 0x00000364; x1 = 0x0000008c
     8c: 000a8213  addi         x4, x21, 0
     90: 000b0293  addi         x5, x22, 0
     94: 00020f93  addi         x31, x4, 0
     98: 00028f13  addi         x30, x5, 0
     9c: 000a3eb7  lui          x29, 0x000a3  # x29 = 0x000a3000
     a0: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000a2800
     a4: 344000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x000000a8
     a8: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     ac: 2b8000ef  jal          x1, 0x00000364  # target 0x00000364; x1 = 0x000000b0
     b0: 000a8213  addi         x4, x21, 0
     b4: 000b0293  addi         x5, x22, 0
     b8: 00020f93  addi         x31, x4, 0
     bc: 00028f13  addi         x30, x5, 0
     c0: 000a3eb7  lui          x29, 0x000a3  # x29 = 0x000a3000
     c4: 324000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x000000c8
     c8: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     cc: 298000ef  jal          x1, 0x00000364  # target 0x00000364; x1 = 0x000000d0
     d0: 000a8213  addi         x4, x21, 0
     d4: 000b0293  addi         x5, x22, 0
     d8: 00020f93  addi         x31, x4, 0
     dc: 00028f13  addi         x30, x5, 0
     e0: 000a4eb7  lui          x29, 0x000a4  # x29 = 0x000a4000
     e4: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000a3800
     e8: 300000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x000000ec
     ec: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     f0: 274000ef  jal          x1, 0x00000364  # target 0x00000364; x1 = 0x000000f4
     f4: 000a8213  addi         x4, x21, 0
     f8: 000b0293  addi         x5, x22, 0
     fc: 00020f93  addi         x31, x4, 0
    100: 00028f13  addi         x30, x5, 0
    104: 000a4eb7  lui          x29, 0x000a4  # x29 = 0x000a4000
    108: 2e0000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x0000010c
    10c: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    110: 37c000ef  jal          x1, 0x0000048c  # target 0x0000048c; x1 = 0x00000114
    114: 000a8213  addi         x4, x21, 0
    118: 000b0293  addi         x5, x22, 0
    11c: 00020f93  addi         x31, x4, 0
    120: 00028f13  addi         x30, x5, 0
    124: 000a5eb7  lui          x29, 0x000a5  # x29 = 0x000a5000
    128: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000a4800
    12c: 2bc000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x00000130
    130: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    134: 358000ef  jal          x1, 0x0000048c  # target 0x0000048c; x1 = 0x00000138
    138: 000a8213  addi         x4, x21, 0
    13c: 000b0293  addi         x5, x22, 0
    140: 00020f93  addi         x31, x4, 0
    144: 00028f13  addi         x30, x5, 0
    148: 000a5eb7  lui          x29, 0x000a5  # x29 = 0x000a5000
    14c: 29c000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x00000150
    150: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    154: 338000ef  jal          x1, 0x0000048c  # target 0x0000048c; x1 = 0x00000158
    158: 000a8213  addi         x4, x21, 0
    15c: 000b0293  addi         x5, x22, 0
    160: 00020f93  addi         x31, x4, 0
    164: 00028f13  addi         x30, x5, 0
    168: 000a6eb7  lui          x29, 0x000a6  # x29 = 0x000a6000
    16c: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000a5800
    170: 278000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x00000174
    174: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    178: 314000ef  jal          x1, 0x0000048c  # target 0x0000048c; x1 = 0x0000017c
    17c: 000a8213  addi         x4, x21, 0
    180: 000b0293  addi         x5, x22, 0
    184: 00020f93  addi         x31, x4, 0
    188: 00028f13  addi         x30, x5, 0
    18c: 000a6eb7  lui          x29, 0x000a6  # x29 = 0x000a6000
    190: 258000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x00000194
    194: 1b4000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x00000198
    198: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    19c: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1a0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    1a4: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    1a8: 00520233  add          x4, x4, x5
    1ac: 000a5337  lui          x6, 0x000a5  # x6 = 0x000a5000
    1b0: 80030313  addi         x6, x6, -2048  # x6 = 0x000a4800
    1b4: 00626663  bltu         x4, x6, 0x000001c0  # target 0x000001c0
    1b8: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    1bc: 40720233  sub          x4, x4, x7
loc_1c0:
    1c0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1c4: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1c8: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1cc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1d0: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1d4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    1d8: 00420213  addi         x4, x4, 4
    1dc: 01021213  slli         x4, x4, 16
    1e0: 01025213  srli         x4, x4, 16
    1e4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1e8: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1ec: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1f0: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    1f4: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    1f8: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    1fc: 0ff0000f  fence        0xf, 0xf
    200: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    204: 04c28293  addi         x5, x5, 76  # x5 = 0x0000804c
    208: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0000804c
    20c: 7c400393  addi         x7, x0, 1988  # x7 = 0x000007c4
    210: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x000007c4
    214: ff82f293  andi         x5, x5, -8
    218: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    21c: 04448493  addi         x9, x9, 68  # x9 = 0x00008044
    220: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x00008044
    224: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    228: 028383b3  mul          x7, x7, x8
    22c: 0073f313  andi         x6, x7, 7
    230: 0033d393  srli         x7, x7, 3
    234: 00b39393  slli         x7, x7, 11
    238: 007282b3  add          x5, x5, x7
    23c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    240: 00020413  addi         x8, x4, 0
loc_244:
    244: 0e83f263  bgeu         x7, x8, 0x00000328  # target 0x00000328
    248: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    24c: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    250: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_254:
    254: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    258: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    25c: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    260: 40a485b3  sub          x11, x9, x10
    264: 01059593  slli         x11, x11, 16
    268: 0105d593  srli         x11, x11, 16
    26c: 04000613  addi         x12, x0, 64  # x12 = 0x00000040
    270: 40b60633  sub          x12, x12, x11
    274: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    278: 00d67663  bgeu         x12, x13, 0x00000284  # target 0x00000284
    27c: 0ff0000f  fence        0xf, 0xf
    280: fd5ff06f  jal          x0, 0x00000254  # target 0x00000254
loc_284:
    284: 0ff0000f  fence        0xf, 0xf
    288: 0a4000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x0000028c
    28c: 0bc000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x00000290
    290: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    294: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    298: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    29c: 00028f93  addi         x31, x5, 0
    2a0: 00030f13  addi         x30, x6, 0
    2a4: 00048e93  addi         x29, x9, 0
    2a8: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    2ac: 264000ef  jal          x1, 0x00000510  # target 0x00000510; x1 = 0x000002b0
    2b0: 000f8293  addi         x5, x31, 0
    2b4: 000f0313  addi         x6, x30, 0
    2b8: 090000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x000002bc
    2bc: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2c0: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2c4: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    2c8: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2cc: 00a484b3  add          x9, x9, x10
    2d0: 000a05b7  lui          x11, 0x000a0  # x11 = 0x000a0000
    2d4: 00b4e663  bltu         x9, x11, 0x000002e0  # target 0x000002e0
    2d8: 00010637  lui          x12, 0x00010  # x12 = 0x00010000
    2dc: 40c484b3  sub          x9, x9, x12
loc_2e0:
    2e0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2e4: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2e8: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    2ec: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2f0: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    2f4: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    2f8: 00448493  addi         x9, x9, 4
    2fc: 01049493  slli         x9, x9, 16
    300: 0104d493  srli         x9, x9, 16
    304: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    308: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    30c: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    310: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    314: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    318: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    31c: 0ff0000f  fence        0xf, 0xf
    320: 00138393  addi         x7, x7, 1
    324: f21ff06f  jal          x0, 0x00000244  # target 0x00000244
loc_328:
    328: 3100006f  jal          x0, 0x00000638  # target 0x00000638
loc_32c:
    32c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    330: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    334: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    338: 000a0463  beq          x20, x0, 0x00000340  # target 0x00000340
    33c: ff1ff06f  jal          x0, 0x0000032c  # target 0x0000032c
loc_340:
    340: 0ff0000f  fence        0xf, 0xf
    344: 00008067  jalr         x0, 0(x1)
loc_348:
    348: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    34c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    350: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    354: 000a0463  beq          x20, x0, 0x0000035c  # target 0x0000035c
    358: ff1ff06f  jal          x0, 0x00000348  # target 0x00000348
loc_35c:
    35c: 0ff0000f  fence        0xf, 0xf
    360: 00008067  jalr         x0, 0(x1)
loc_364:
    364: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    368: 000aaa03  lw           x20, 0(x21)  # param e2e_context_decode_token; 0x000007c0
    36c: 007a7d13  andi         x26, x20, 7
    370: ff8a7a13  andi         x20, x20, -8
    374: 01af8ab3  add          x21, x31, x26
    378: 007afb93  andi         x23, x21, 7
    37c: 003ada93  srli         x21, x21, 3
    380: 00ba9a93  slli         x21, x21, 11
    384: 014a8ab3  add          x21, x21, x20
    388: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000388
    38c: 030b0b13  addi         x22, x22, 48  # x22 = 0x000003b8
    390: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    394: 050e8e93  addi         x29, x29, 80  # x29 = 0x00008050
    398: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00008050
    39c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    3a0: 03cd8db3  mul          x27, x27, x28
    3a4: 01bb0b33  add          x22, x22, x27
    3a8: 001b9b93  slli         x23, x23, 1
    3ac: 017b0b33  add          x22, x22, x23
    3b0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    3b4: 00008067  jalr         x0, 0(x1)
    3b8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3bc: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3c0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    3c4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    3c8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3cc: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3d0: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    3d4: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    3d8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    3dc: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3e0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    3e4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_3e8:
    3e8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3ec: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    3f0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    3f4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    3f8: 015a6463  bltu         x20, x21, 0x00000400  # target 0x00000400
    3fc: fedff06f  jal          x0, 0x000003e8  # target 0x000003e8
loc_400:
    400: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    404: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    408: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    40c: 014a1a13  slli         x20, x20, 20
    410: 014a5a13  srli         x20, x20, 20
    414: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_418:
    418: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    41c: 000b0463  beq          x22, x0, 0x00000424  # target 0x00000424
    420: ff9ff06f  jal          x0, 0x00000418  # target 0x00000418
loc_424:
    424: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    428: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    42c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    430: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    434: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    438: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    43c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    440: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    444: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    448: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    44c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    450: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    454: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    458: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    45c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    460: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    464: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    468: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    46c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    470: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    474: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    478: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_47c:
    47c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    480: 000b0463  beq          x22, x0, 0x00000488  # target 0x00000488
    484: ff9ff06f  jal          x0, 0x0000047c  # target 0x0000047c
loc_488:
    488: 00008067  jalr         x0, 0(x1)
loc_48c:
    48c: 7dc00a93  addi         x21, x0, 2012  # x21 = 0x000007dc
    490: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x000007dc
    494: 007a7d13  andi         x26, x20, 7
    498: ff8a7a13  andi         x20, x20, -8
    49c: 01af8ab3  add          x21, x31, x26
    4a0: 007afb93  andi         x23, x21, 7
    4a4: 003ada93  srli         x21, x21, 3
    4a8: 00ba9a93  slli         x21, x21, 11
    4ac: 014a8ab3  add          x21, x21, x20
    4b0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004b0
    4b4: 030b0b13  addi         x22, x22, 48  # x22 = 0x000004e0
    4b8: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    4bc: 050e8e93  addi         x29, x29, 80  # x29 = 0x00008050
    4c0: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00008050
    4c4: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    4c8: 03cd8db3  mul          x27, x27, x28
    4cc: 01bb0b33  add          x22, x22, x27
    4d0: 001b9b93  slli         x23, x23, 1
    4d4: 017b0b33  add          x22, x22, x23
    4d8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4dc: 00008067  jalr         x0, 0(x1)
    4e0: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4e4: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4e8: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4ec: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    4f0: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f4: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f8: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    4fc: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    500: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    504: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    508: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    50c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_510:
    510: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000510
    514: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x00000608
    518: 00008cb7  lui          x25, 0x00008  # x25 = 0x00008000
    51c: 050c8c93  addi         x25, x25, 80  # x25 = 0x00008050
    520: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x00008050
    524: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    528: 038b8bb3  mul          x23, x23, x24
    52c: 017a0a33  add          x20, x20, x23
loc_530:
    530: 001f1a93  slli         x21, x30, 1
    534: 014a8ab3  add          x21, x21, x20
    538: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_53c:
    53c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    540: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    544: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    548: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    54c: 018be463  bltu         x23, x24, 0x00000554  # target 0x00000554
    550: fedff06f  jal          x0, 0x0000053c  # target 0x0000053c
loc_554:
    554: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    558: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    55c: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    560: 014b9b93  slli         x23, x23, 20
    564: 014bdb93  srli         x23, x23, 20
    568: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_56c:
    56c: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    570: 000c8463  beq          x25, x0, 0x00000578  # target 0x00000578
    574: ff9ff06f  jal          x0, 0x0000056c  # target 0x0000056c
loc_578:
    578: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    57c: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    580: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    584: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    588: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    58c: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    590: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    594: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    598: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    59c: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    5a0: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    5a4: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    5a8: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5ac: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    5b0: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    5b4: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    5b8: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    5bc: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    5c0: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    5c4: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    5c8: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    5cc: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_5d0:
    5d0: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    5d4: 000c8463  beq          x25, x0, 0x000005dc  # target 0x000005dc
    5d8: ff9ff06f  jal          x0, 0x000005d0  # target 0x000005d0
loc_5dc:
    5dc: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5e0: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    5e4: 016e8eb3  add          x29, x29, x22
    5e8: 001f0f13  addi         x30, x30, 1
    5ec: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    5f0: 015f1663  bne          x30, x21, 0x000005fc  # target 0x000005fc
    5f4: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    5f8: 016f8fb3  add          x31, x31, x22
loc_5fc:
    5fc: fffe0e13  addi         x28, x28, -1
    600: f20e18e3  bne          x28, x0, 0x00000530  # target 0x00000530
    604: 00008067  jalr         x0, 0(x1)
    608: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    60c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    610: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    614: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    618: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    61c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    620: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    624: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    628: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    62c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    630: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    634: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    638:           j FW_BRISC+4   # return to firmware, linked at install
