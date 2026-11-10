# llama3 8b-bf16 decode: down, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (48): 1,2 2,2 3,2 4,2 5,2 6,2 1,3 2,3 3,3 4,3 5,3 6,3 1,4 2,4 3,4 4,4 5,4 6,4 1,5 2,5 3,5 4,5 5,5 6,5 1,6 2,6 3,6 4,6 5,6 6,6 1,7 2,7 3,7 4,7 5,7 6,7 1,8 2,8 3,8 4,8 5,8 6,8 1,9 2,9 3,9 4,9 5,9 6,9
# params: 0x780=e2e_hidden_dense_decode_token, 0x784=e2e_l0_down, 0x788=e2e_x_a, 0x78c=e2e_x_b, 0xe980=e2e_q_compact, 0xe984=e2e_l0_down_row_start, 0xe988=dense_start, 0xe98c=e2e_l0_down_rows
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
      8: 0000f537  lui          x10, 0x0000f  # x10 = 0x0000f000
      c: fc050513  addi         x10, x10, -64  # x10 = 0x0000efc0
     10: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0000efc0
     14: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     18: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: 3c4000ef  jal          x1, 0x000003e4  # target 0x000003e4; x1 = 0x00000024
     24: 3dc000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x00000028
     28: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     2c: 3f0000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000030
     30: 000a8213  addi         x4, x21, 0
     34: 000b0293  addi         x5, x22, 0
     38: 00020f93  addi         x31, x4, 0
     3c: 00028f13  addi         x30, x5, 0
     40: 0001eeb7  lui          x29, 0x0001e  # x29 = 0x0001e000
     44: fc0e8e93  addi         x29, x29, -64  # x29 = 0x0001dfc0
     48: 420000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x0000004c
     4c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     50: 3cc000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000054
     54: 000a8213  addi         x4, x21, 0
     58: 000b0293  addi         x5, x22, 0
     5c: 00020f93  addi         x31, x4, 0
     60: 00028f13  addi         x30, x5, 0
     64: 0001eeb7  lui          x29, 0x0001e  # x29 = 0x0001e000
     68: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x0001e7c0
     6c: 3fc000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000070
     70: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     74: 3a8000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000078
     78: 000a8213  addi         x4, x21, 0
     7c: 000b0293  addi         x5, x22, 0
     80: 00020f93  addi         x31, x4, 0
     84: 00028f13  addi         x30, x5, 0
     88: 0001feb7  lui          x29, 0x0001f  # x29 = 0x0001f000
     8c: fc0e8e93  addi         x29, x29, -64  # x29 = 0x0001efc0
     90: 3d8000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000094
     94: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     98: 384000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x0000009c
     9c: 000a8213  addi         x4, x21, 0
     a0: 000b0293  addi         x5, x22, 0
     a4: 00020f93  addi         x31, x4, 0
     a8: 00028f13  addi         x30, x5, 0
     ac: 0001feb7  lui          x29, 0x0001f  # x29 = 0x0001f000
     b0: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x0001f7c0
     b4: 3b4000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x000000b8
     b8: 00400f93  addi         x31, x0, 4  # x31 = 0x00000004
     bc: 360000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x000000c0
     c0: 000a8213  addi         x4, x21, 0
     c4: 000b0293  addi         x5, x22, 0
     c8: 00020f93  addi         x31, x4, 0
     cc: 00028f13  addi         x30, x5, 0
     d0: 00020eb7  lui          x29, 0x00020  # x29 = 0x00020000
     d4: fc0e8e93  addi         x29, x29, -64  # x29 = 0x0001ffc0
     d8: 390000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x000000dc
     dc: 00500f93  addi         x31, x0, 5  # x31 = 0x00000005
     e0: 33c000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x000000e4
     e4: 000a8213  addi         x4, x21, 0
     e8: 000b0293  addi         x5, x22, 0
     ec: 00020f93  addi         x31, x4, 0
     f0: 00028f13  addi         x30, x5, 0
     f4: 00020eb7  lui          x29, 0x00020  # x29 = 0x00020000
     f8: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000207c0
     fc: 36c000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000100
    100: 00600f93  addi         x31, x0, 6  # x31 = 0x00000006
    104: 318000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000108
    108: 000a8213  addi         x4, x21, 0
    10c: 000b0293  addi         x5, x22, 0
    110: 00020f93  addi         x31, x4, 0
    114: 00028f13  addi         x30, x5, 0
    118: 00021eb7  lui          x29, 0x00021  # x29 = 0x00021000
    11c: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00020fc0
    120: 348000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000124
    124: 00700f93  addi         x31, x0, 7  # x31 = 0x00000007
    128: 2f4000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x0000012c
    12c: 000a8213  addi         x4, x21, 0
    130: 000b0293  addi         x5, x22, 0
    134: 00020f93  addi         x31, x4, 0
    138: 00028f13  addi         x30, x5, 0
    13c: 00021eb7  lui          x29, 0x00021  # x29 = 0x00021000
    140: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000217c0
    144: 324000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000148
    148: 00800f93  addi         x31, x0, 8  # x31 = 0x00000008
    14c: 2d0000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000150
    150: 000a8213  addi         x4, x21, 0
    154: 000b0293  addi         x5, x22, 0
    158: 00020f93  addi         x31, x4, 0
    15c: 00028f13  addi         x30, x5, 0
    160: 00022eb7  lui          x29, 0x00022  # x29 = 0x00022000
    164: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00021fc0
    168: 300000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x0000016c
    16c: 00900f93  addi         x31, x0, 9  # x31 = 0x00000009
    170: 2ac000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000174
    174: 000a8213  addi         x4, x21, 0
    178: 000b0293  addi         x5, x22, 0
    17c: 00020f93  addi         x31, x4, 0
    180: 00028f13  addi         x30, x5, 0
    184: 00022eb7  lui          x29, 0x00022  # x29 = 0x00022000
    188: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000227c0
    18c: 2dc000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000190
    190: 00a00f93  addi         x31, x0, 10  # x31 = 0x0000000a
    194: 288000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000198
    198: 000a8213  addi         x4, x21, 0
    19c: 000b0293  addi         x5, x22, 0
    1a0: 00020f93  addi         x31, x4, 0
    1a4: 00028f13  addi         x30, x5, 0
    1a8: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    1ac: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00022fc0
    1b0: 2b8000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x000001b4
    1b4: 00b00f93  addi         x31, x0, 11  # x31 = 0x0000000b
    1b8: 264000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x000001bc
    1bc: 000a8213  addi         x4, x21, 0
    1c0: 000b0293  addi         x5, x22, 0
    1c4: 00020f93  addi         x31, x4, 0
    1c8: 00028f13  addi         x30, x5, 0
    1cc: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    1d0: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000237c0
    1d4: 294000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x000001d8
    1d8: 00c00f93  addi         x31, x0, 12  # x31 = 0x0000000c
    1dc: 240000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x000001e0
    1e0: 000a8213  addi         x4, x21, 0
    1e4: 000b0293  addi         x5, x22, 0
    1e8: 00020f93  addi         x31, x4, 0
    1ec: 00028f13  addi         x30, x5, 0
    1f0: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    1f4: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00023fc0
    1f8: 270000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x000001fc
    1fc: 00d00f93  addi         x31, x0, 13  # x31 = 0x0000000d
    200: 21c000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000204
    204: 000a8213  addi         x4, x21, 0
    208: 000b0293  addi         x5, x22, 0
    20c: 00020f93  addi         x31, x4, 0
    210: 00028f13  addi         x30, x5, 0
    214: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    218: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000247c0
    21c: 24c000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000220
    220: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    224: 2e8000ef  jal          x1, 0x0000050c  # target 0x0000050c; x1 = 0x00000228
    228: 000a8213  addi         x4, x21, 0
    22c: 000b0293  addi         x5, x22, 0
    230: 00020f93  addi         x31, x4, 0
    234: 00028f13  addi         x30, x5, 0
    238: 00025eb7  lui          x29, 0x00025  # x29 = 0x00025000
    23c: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000257c0
    240: 228000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000244
    244: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    248: 2c4000ef  jal          x1, 0x0000050c  # target 0x0000050c; x1 = 0x0000024c
    24c: 000a8213  addi         x4, x21, 0
    250: 000b0293  addi         x5, x22, 0
    254: 00020f93  addi         x31, x4, 0
    258: 00028f13  addi         x30, x5, 0
    25c: 00026eb7  lui          x29, 0x00026  # x29 = 0x00026000
    260: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00025fc0
    264: 204000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000268
    268: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    26c: 2a0000ef  jal          x1, 0x0000050c  # target 0x0000050c; x1 = 0x00000270
    270: 000a8213  addi         x4, x21, 0
    274: 000b0293  addi         x5, x22, 0
    278: 00020f93  addi         x31, x4, 0
    27c: 00028f13  addi         x30, x5, 0
    280: 00026eb7  lui          x29, 0x00026  # x29 = 0x00026000
    284: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000267c0
    288: 1e0000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x0000028c
    28c: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    290: 27c000ef  jal          x1, 0x0000050c  # target 0x0000050c; x1 = 0x00000294
    294: 000a8213  addi         x4, x21, 0
    298: 000b0293  addi         x5, x22, 0
    29c: 00020f93  addi         x31, x4, 0
    2a0: 00028f13  addi         x30, x5, 0
    2a4: 00027eb7  lui          x29, 0x00027  # x29 = 0x00027000
    2a8: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00026fc0
    2ac: 1bc000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x000002b0
    2b0: 150000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x000002b4
    2b4: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    2b8: 98c28293  addi         x5, x5, -1652  # x5 = 0x0000e98c
    2bc: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0000e98c
    2c0: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    2c4: 0003a283  lw           x5, 0(x7)  # param e2e_l0_down; 0x00000784
    2c8: ff82f293  andi         x5, x5, -8
    2cc: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    2d0: 98448493  addi         x9, x9, -1660  # x9 = 0x0000e984
    2d4: 0004a383  lw           x7, 0(x9)  # param e2e_l0_down_row_start; 0x0000e984
    2d8: 00e00413  addi         x8, x0, 14  # x8 = 0x0000000e
    2dc: 028383b3  mul          x7, x7, x8
    2e0: 0073f313  andi         x6, x7, 7
    2e4: 0033d393  srli         x7, x7, 3
    2e8: 00b39393  slli         x7, x7, 11
    2ec: 007282b3  add          x5, x5, x7
    2f0: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    2f4: 00020413  addi         x8, x4, 0
loc_2f8:
    2f8: 0e83f463  bgeu         x7, x8, 0x000003e0  # target 0x000003e0
    2fc: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    300: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    304: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_308:
    308: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    30c: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    310: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    314: 40a485b3  sub          x11, x9, x10
    318: 01059593  slli         x11, x11, 16
    31c: 0105d593  srli         x11, x11, 16
    320: 01c00613  addi         x12, x0, 28  # x12 = 0x0000001c
    324: 40b60633  sub          x12, x12, x11
    328: 00e00693  addi         x13, x0, 14  # x13 = 0x0000000e
    32c: 00d67663  bgeu         x12, x13, 0x00000338  # target 0x00000338
    330: 0ff0000f  fence        0xf, 0xf
    334: fd5ff06f  jal          x0, 0x00000308  # target 0x00000308
loc_338:
    338: 0ff0000f  fence        0xf, 0xf
    33c: 0a8000ef  jal          x1, 0x000003e4  # target 0x000003e4; x1 = 0x00000340
    340: 0c0000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x00000344
    344: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    348: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    34c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    350: 00028f93  addi         x31, x5, 0
    354: 00030f13  addi         x30, x6, 0
    358: 00048e93  addi         x29, x9, 0
    35c: 00e00e13  addi         x28, x0, 14  # x28 = 0x0000000e
    360: 1f8000ef  jal          x1, 0x00000558  # target 0x00000558; x1 = 0x00000364
    364: 000f8293  addi         x5, x31, 0
    368: 000f0313  addi         x6, x30, 0
    36c: 094000ef  jal          x1, 0x00000400  # target 0x00000400; x1 = 0x00000370
    370: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    374: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    378: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    37c: 00007537  lui          x10, 0x00007  # x10 = 0x00007000
    380: 00a484b3  add          x9, x9, x10
    384: 0001d5b7  lui          x11, 0x0001d  # x11 = 0x0001d000
    388: fc058593  addi         x11, x11, -64  # x11 = 0x0001cfc0
    38c: 00b4e663  bltu         x9, x11, 0x00000398  # target 0x00000398
    390: 0000e637  lui          x12, 0x0000e  # x12 = 0x0000e000
    394: 40c484b3  sub          x9, x9, x12
loc_398:
    398: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    39c: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    3a0: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    3a4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3a8: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    3ac: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    3b0: 00e48493  addi         x9, x9, 14
    3b4: 01049493  slli         x9, x9, 16
    3b8: 0104d493  srli         x9, x9, 16
    3bc: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3c0: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    3c4: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    3c8: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    3cc: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    3d0: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    3d4: 0ff0000f  fence        0xf, 0xf
    3d8: 00138393  addi         x7, x7, 1
    3dc: f1dff06f  jal          x0, 0x000002f8  # target 0x000002f8
loc_3e0:
    3e0: 2680006f  jal          x0, 0x00000648  # target 0x00000648
loc_3e4:
    3e4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3e8: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    3ec: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    3f0: 000a0463  beq          x20, x0, 0x000003f8  # target 0x000003f8
    3f4: ff1ff06f  jal          x0, 0x000003e4  # target 0x000003e4
loc_3f8:
    3f8: 0ff0000f  fence        0xf, 0xf
    3fc: 00008067  jalr         x0, 0(x1)
loc_400:
    400: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    404: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    408: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    40c: 000a0463  beq          x20, x0, 0x00000414  # target 0x00000414
    410: ff1ff06f  jal          x0, 0x00000400  # target 0x00000400
loc_414:
    414: 0ff0000f  fence        0xf, 0xf
    418: 00008067  jalr         x0, 0(x1)
loc_41c:
    41c: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    420: 000aaa03  lw           x20, 0(x21)  # param e2e_hidden_dense_decode_token; 0x00000780
    424: 007a7d13  andi         x26, x20, 7
    428: ff8a7a13  andi         x20, x20, -8
    42c: 01af8ab3  add          x21, x31, x26
    430: 007afb93  andi         x23, x21, 7
    434: 003ada93  srli         x21, x21, 3
    438: 00ba9a93  slli         x21, x21, 11
    43c: 014a8ab3  add          x21, x21, x20
    440: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000440
    444: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000458
    448: 001b9b93  slli         x23, x23, 1
    44c: 017b0b33  add          x22, x22, x23
    450: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    454: 00008067  jalr         x0, 0(x1)
    458: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    45c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    460: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    464: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_468:
    468: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    46c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    470: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    474: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    478: 015a6463  bltu         x20, x21, 0x00000480  # target 0x00000480
    47c: fedff06f  jal          x0, 0x00000468  # target 0x00000468
loc_480:
    480: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    484: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    488: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    48c: 014a1a13  slli         x20, x20, 20
    490: 014a5a13  srli         x20, x20, 20
    494: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_498:
    498: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    49c: 000b0463  beq          x22, x0, 0x000004a4  # target 0x000004a4
    4a0: ff9ff06f  jal          x0, 0x00000498  # target 0x00000498
loc_4a4:
    4a4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    4a8: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    4ac: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    4b0: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    4b4: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    4b8: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    4bc: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    4c0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    4c4: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    4c8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    4cc: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    4d0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    4d4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4d8: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    4dc: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    4e0: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    4e4: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    4e8: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    4ec: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    4f0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    4f4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    4f8: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_4fc:
    4fc: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    500: 000b0463  beq          x22, x0, 0x00000508  # target 0x00000508
    504: ff9ff06f  jal          x0, 0x000004fc  # target 0x000004fc
loc_508:
    508: 00008067  jalr         x0, 0(x1)
loc_50c:
    50c: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    510: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b; 0x0000078c
    514: 007a7d13  andi         x26, x20, 7
    518: ff8a7a13  andi         x20, x20, -8
    51c: 01af8ab3  add          x21, x31, x26
    520: 007afb93  andi         x23, x21, 7
    524: 003ada93  srli         x21, x21, 3
    528: 00ba9a93  slli         x21, x21, 11
    52c: 014a8ab3  add          x21, x21, x20
    530: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000530
    534: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000548
    538: 001b9b93  slli         x23, x23, 1
    53c: 017b0b33  add          x22, x22, x23
    540: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    544: 00008067  jalr         x0, 0(x1)
    548: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    54c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    550: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    554: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_558:
    558: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000558
    55c: 0e0a0a13  addi         x20, x20, 224  # x20 = 0x00000638
loc_560:
    560: 001f1a93  slli         x21, x30, 1
    564: 014a8ab3  add          x21, x21, x20
    568: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_56c:
    56c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    570: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    574: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    578: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    57c: 018be463  bltu         x23, x24, 0x00000584  # target 0x00000584
    580: fedff06f  jal          x0, 0x0000056c  # target 0x0000056c
loc_584:
    584: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    588: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    58c: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    590: 014b9b93  slli         x23, x23, 20
    594: 014bdb93  srli         x23, x23, 20
    598: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_59c:
    59c: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    5a0: 000c8463  beq          x25, x0, 0x000005a8  # target 0x000005a8
    5a4: ff9ff06f  jal          x0, 0x0000059c  # target 0x0000059c
loc_5a8:
    5a8: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    5ac: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    5b0: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    5b4: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    5b8: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    5bc: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    5c0: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    5c4: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    5c8: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    5cc: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    5d0: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    5d4: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    5d8: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5dc: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    5e0: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    5e4: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    5e8: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    5ec: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    5f0: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    5f4: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    5f8: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    5fc: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_600:
    600: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    604: 000c8463  beq          x25, x0, 0x0000060c  # target 0x0000060c
    608: ff9ff06f  jal          x0, 0x00000600  # target 0x00000600
loc_60c:
    60c: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    610: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    614: 016e8eb3  add          x29, x29, x22
    618: 001f0f13  addi         x30, x30, 1
    61c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    620: 015f1663  bne          x30, x21, 0x0000062c  # target 0x0000062c
    624: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    628: 016f8fb3  add          x31, x31, x22
loc_62c:
    62c: fffe0e13  addi         x28, x28, -1
    630: f20e18e3  bne          x28, x0, 0x00000560  # target 0x00000560
    634: 00008067  jalr         x0, 0(x1)
    638: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    63c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    640: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    644: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    648:           j FW_BRISC+4   # return to firmware, linked at install
