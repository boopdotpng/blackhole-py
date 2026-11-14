# llama3 8b-bf16 decode: down, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (40): 7,2 10,2 11,2 12,2 13,2 7,3 10,3 11,3 12,3 13,3 7,4 10,4 11,4 12,4 13,4 7,5 10,5 11,5 12,5 13,5 7,6 10,6 11,6 12,6 13,6 7,7 10,7 11,7 12,7 13,7 7,8 10,8 11,8 12,8 13,8 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_hidden_dense_decode_token, 0x784=e2e_l0_down, 0x788=e2e_x_a, 0x78c=e2e_x_b, 0x11980=e2e_q_compact, 0x11984=e2e_l0_down_row_start, 0x11988=dense_start, 0x1198c=e2e_l0_down_rows
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
      8: 00012537  lui          x10, 0x00012  # x10 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
      c: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00012000
     10: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     14: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: 39c000ef  jal          x1, 0x000003b8  # target 0x000003b8; x1 = 0x00000020
     20: 3b4000ef  jal          x1, 0x000003d4  # target 0x000003d4; x1 = 0x00000024
     24: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     28: 3c8000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x0000002c
     2c: 000a8213  addi         x4, x21, 0
     30: 000b0293  addi         x5, x22, 0
     34: 00020f93  addi         x31, x4, 0
     38: 00028f13  addi         x30, x5, 0
     3c: 00021eb7  lui          x29, 0x00021  # x29 = 0x00021000
     40: 3fc000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000044
     44: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     48: 3a8000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x0000004c
     4c: 000a8213  addi         x4, x21, 0
     50: 000b0293  addi         x5, x22, 0
     54: 00020f93  addi         x31, x4, 0
     58: 00028f13  addi         x30, x5, 0
     5c: 00022eb7  lui          x29, 0x00022  # x29 = 0x00022000
     60: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00021800
     64: 3d8000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000068
     68: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     6c: 384000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x00000070
     70: 000a8213  addi         x4, x21, 0
     74: 000b0293  addi         x5, x22, 0
     78: 00020f93  addi         x31, x4, 0
     7c: 00028f13  addi         x30, x5, 0
     80: 00022eb7  lui          x29, 0x00022  # x29 = 0x00022000
     84: 3b8000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000088
     88: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     8c: 364000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
     a4: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00022800
     a8: 394000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x000000ac
     ac: 00400f93  addi         x31, x0, 4  # x31 = 0x00000004
     b0: 340000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
     c8: 374000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x000000cc
     cc: 00500f93  addi         x31, x0, 5  # x31 = 0x00000005
     d0: 320000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x000000d4
     d4: 000a8213  addi         x4, x21, 0
     d8: 000b0293  addi         x5, x22, 0
     dc: 00020f93  addi         x31, x4, 0
     e0: 00028f13  addi         x30, x5, 0
     e4: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
     e8: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00023800
     ec: 350000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x000000f0
     f0: 00600f93  addi         x31, x0, 6  # x31 = 0x00000006
     f4: 2fc000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x000000f8
     f8: 000a8213  addi         x4, x21, 0
     fc: 000b0293  addi         x5, x22, 0
    100: 00020f93  addi         x31, x4, 0
    104: 00028f13  addi         x30, x5, 0
    108: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    10c: 330000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000110
    110: 00700f93  addi         x31, x0, 7  # x31 = 0x00000007
    114: 2dc000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x00000118
    118: 000a8213  addi         x4, x21, 0
    11c: 000b0293  addi         x5, x22, 0
    120: 00020f93  addi         x31, x4, 0
    124: 00028f13  addi         x30, x5, 0
    128: 00025eb7  lui          x29, 0x00025  # x29 = 0x00025000
    12c: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00024800
    130: 30c000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000134
    134: 00800f93  addi         x31, x0, 8  # x31 = 0x00000008
    138: 2b8000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x0000013c
    13c: 000a8213  addi         x4, x21, 0
    140: 000b0293  addi         x5, x22, 0
    144: 00020f93  addi         x31, x4, 0
    148: 00028f13  addi         x30, x5, 0
    14c: 00025eb7  lui          x29, 0x00025  # x29 = 0x00025000
    150: 2ec000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000154
    154: 00900f93  addi         x31, x0, 9  # x31 = 0x00000009
    158: 298000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x0000015c
    15c: 000a8213  addi         x4, x21, 0
    160: 000b0293  addi         x5, x22, 0
    164: 00020f93  addi         x31, x4, 0
    168: 00028f13  addi         x30, x5, 0
    16c: 00026eb7  lui          x29, 0x00026  # x29 = 0x00026000
    170: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00025800
    174: 2c8000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000178
    178: 00a00f93  addi         x31, x0, 10  # x31 = 0x0000000a
    17c: 274000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x00000180
    180: 000a8213  addi         x4, x21, 0
    184: 000b0293  addi         x5, x22, 0
    188: 00020f93  addi         x31, x4, 0
    18c: 00028f13  addi         x30, x5, 0
    190: 00026eb7  lui          x29, 0x00026  # x29 = 0x00026000
    194: 2a8000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000198
    198: 00b00f93  addi         x31, x0, 11  # x31 = 0x0000000b
    19c: 254000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x000001a0
    1a0: 000a8213  addi         x4, x21, 0
    1a4: 000b0293  addi         x5, x22, 0
    1a8: 00020f93  addi         x31, x4, 0
    1ac: 00028f13  addi         x30, x5, 0
    1b0: 00027eb7  lui          x29, 0x00027  # x29 = 0x00027000
    1b4: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00026800
    1b8: 284000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x000001bc
    1bc: 00c00f93  addi         x31, x0, 12  # x31 = 0x0000000c
    1c0: 230000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x000001c4
    1c4: 000a8213  addi         x4, x21, 0
    1c8: 000b0293  addi         x5, x22, 0
    1cc: 00020f93  addi         x31, x4, 0
    1d0: 00028f13  addi         x30, x5, 0
    1d4: 00027eb7  lui          x29, 0x00027  # x29 = 0x00027000
    1d8: 264000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x000001dc
    1dc: 00d00f93  addi         x31, x0, 13  # x31 = 0x0000000d
    1e0: 210000ef  jal          x1, 0x000003f0  # target 0x000003f0; x1 = 0x000001e4
    1e4: 000a8213  addi         x4, x21, 0
    1e8: 000b0293  addi         x5, x22, 0
    1ec: 00020f93  addi         x31, x4, 0
    1f0: 00028f13  addi         x30, x5, 0
    1f4: 00028eb7  lui          x29, 0x00028  # x29 = 0x00028000
    1f8: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00027800
    1fc: 240000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000200
    200: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    204: 2dc000ef  jal          x1, 0x000004e0  # target 0x000004e0; x1 = 0x00000208
    208: 000a8213  addi         x4, x21, 0
    20c: 000b0293  addi         x5, x22, 0
    210: 00020f93  addi         x31, x4, 0
    214: 00028f13  addi         x30, x5, 0
    218: 00029eb7  lui          x29, 0x00029  # x29 = 0x00029000
    21c: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00028800
    220: 21c000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000224
    224: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    228: 2b8000ef  jal          x1, 0x000004e0  # target 0x000004e0; x1 = 0x0000022c
    22c: 000a8213  addi         x4, x21, 0
    230: 000b0293  addi         x5, x22, 0
    234: 00020f93  addi         x31, x4, 0
    238: 00028f13  addi         x30, x5, 0
    23c: 00029eb7  lui          x29, 0x00029  # x29 = 0x00029000
    240: 1fc000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000244
    244: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    248: 298000ef  jal          x1, 0x000004e0  # target 0x000004e0; x1 = 0x0000024c
    24c: 000a8213  addi         x4, x21, 0
    250: 000b0293  addi         x5, x22, 0
    254: 00020f93  addi         x31, x4, 0
    258: 00028f13  addi         x30, x5, 0
    25c: 0002aeb7  lui          x29, 0x0002a  # x29 = 0x0002a000
    260: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00029800
    264: 1d8000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000268
    268: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    26c: 274000ef  jal          x1, 0x000004e0  # target 0x000004e0; x1 = 0x00000270
    270: 000a8213  addi         x4, x21, 0
    274: 000b0293  addi         x5, x22, 0
    278: 00020f93  addi         x31, x4, 0
    27c: 00028f13  addi         x30, x5, 0
    280: 0002aeb7  lui          x29, 0x0002a  # x29 = 0x0002a000
    284: 1b8000ef  jal          x1, 0x0000043c  # target 0x0000043c; x1 = 0x00000288
    288: 14c000ef  jal          x1, 0x000003d4  # target 0x000003d4; x1 = 0x0000028c
    28c: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    290: 98c28293  addi         x5, x5, -1652  # x5 = 0x0001198c
    294: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0001198c
    298: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    29c: 0003a283  lw           x5, 0(x7)  # param e2e_l0_down; 0x00000784
    2a0: ff82f293  andi         x5, x5, -8
    2a4: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2a8: 98448493  addi         x9, x9, -1660  # x9 = 0x00011984
    2ac: 0004a383  lw           x7, 0(x9)  # param e2e_l0_down_row_start; 0x00011984
    2b0: 00e00413  addi         x8, x0, 14  # x8 = 0x0000000e
    2b4: 028383b3  mul          x7, x7, x8
    2b8: 0073f313  andi         x6, x7, 7
    2bc: 0033d393  srli         x7, x7, 3
    2c0: 00b39393  slli         x7, x7, 11
    2c4: 007282b3  add          x5, x5, x7
    2c8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    2cc: 00020413  addi         x8, x4, 0
loc_2d0:
    2d0: 0e83f263  bgeu         x7, x8, 0x000003b4  # target 0x000003b4
    2d4: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    2d8: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    2dc: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_2e0:
    2e0: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    2e4: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    2e8: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    2ec: 40a485b3  sub          x11, x9, x10
    2f0: 01059593  slli         x11, x11, 16
    2f4: 0105d593  srli         x11, x11, 16
    2f8: 01c00613  addi         x12, x0, 28  # x12 = 0x0000001c
    2fc: 40b60633  sub          x12, x12, x11
    300: 00e00693  addi         x13, x0, 14  # x13 = 0x0000000e
    304: 00d67663  bgeu         x12, x13, 0x00000310  # target 0x00000310
    308: 0ff0000f  fence        0xf, 0xf
    30c: fd5ff06f  jal          x0, 0x000002e0  # target 0x000002e0
loc_310:
    310: 0ff0000f  fence        0xf, 0xf
    314: 0a4000ef  jal          x1, 0x000003b8  # target 0x000003b8; x1 = 0x00000318
    318: 0bc000ef  jal          x1, 0x000003d4  # target 0x000003d4; x1 = 0x0000031c
    31c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    320: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    324: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    328: 00028f93  addi         x31, x5, 0
    32c: 00030f13  addi         x30, x6, 0
    330: 00048e93  addi         x29, x9, 0
    334: 00e00e13  addi         x28, x0, 14  # x28 = 0x0000000e
    338: 1f4000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x0000033c
    33c: 000f8293  addi         x5, x31, 0
    340: 000f0313  addi         x6, x30, 0
    344: 090000ef  jal          x1, 0x000003d4  # target 0x000003d4; x1 = 0x00000348
    348: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    34c: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    350: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    354: 00007537  lui          x10, 0x00007  # x10 = 0x00007000
    358: 00a484b3  add          x9, x9, x10
    35c: 000205b7  lui          x11, 0x00020  # x11 = 0x00020000
    360: 00b4e663  bltu         x9, x11, 0x0000036c  # target 0x0000036c
    364: 0000e637  lui          x12, 0x0000e  # x12 = 0x0000e000
    368: 40c484b3  sub          x9, x9, x12
loc_36c:
    36c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    370: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    374: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    378: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    37c: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    380: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    384: 00e48493  addi         x9, x9, 14
    388: 01049493  slli         x9, x9, 16
    38c: 0104d493  srli         x9, x9, 16
    390: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    394: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    398: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    39c: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    3a0: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    3a4: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    3a8: 0ff0000f  fence        0xf, 0xf
    3ac: 00138393  addi         x7, x7, 1
    3b0: f21ff06f  jal          x0, 0x000002d0  # target 0x000002d0
loc_3b4:
    3b4: 2680006f  jal          x0, 0x0000061c  # target 0x0000061c
loc_3b8:
    3b8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    3bc: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    3c0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    3c4: 000a0463  beq          x20, x0, 0x000003cc  # target 0x000003cc
    3c8: ff1ff06f  jal          x0, 0x000003b8  # target 0x000003b8
loc_3cc:
    3cc: 0ff0000f  fence        0xf, 0xf
    3d0: 00008067  jalr         x0, 0(x1)
loc_3d4:
    3d4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    3d8: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    3dc: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    3e0: 000a0463  beq          x20, x0, 0x000003e8  # target 0x000003e8
    3e4: ff1ff06f  jal          x0, 0x000003d4  # target 0x000003d4
loc_3e8:
    3e8: 0ff0000f  fence        0xf, 0xf
    3ec: 00008067  jalr         x0, 0(x1)
loc_3f0:
    3f0: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    3f4: 000aaa03  lw           x20, 0(x21)  # param e2e_hidden_dense_decode_token; 0x00000780
    3f8: 007a7d13  andi         x26, x20, 7
    3fc: ff8a7a13  andi         x20, x20, -8
    400: 01af8ab3  add          x21, x31, x26
    404: 007afb93  andi         x23, x21, 7
    408: 003ada93  srli         x21, x21, 3
    40c: 00ba9a93  slli         x21, x21, 11
    410: 014a8ab3  add          x21, x21, x20
    414: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000414
    418: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000042c
    41c: 001b9b93  slli         x23, x23, 1
    420: 017b0b33  add          x22, x22, x23
    424: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    428: 00008067  jalr         x0, 0(x1)
    42c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    430: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    434: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    438: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_43c:
    43c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    440: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    444: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    448: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    44c: 015a6463  bltu         x20, x21, 0x00000454  # target 0x00000454
    450: fedff06f  jal          x0, 0x0000043c  # target 0x0000043c
loc_454:
    454: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    458: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    45c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    460: 014a1a13  slli         x20, x20, 20
    464: 014a5a13  srli         x20, x20, 20
    468: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_46c:
    46c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    470: 000b0463  beq          x22, x0, 0x00000478  # target 0x00000478
    474: ff9ff06f  jal          x0, 0x0000046c  # target 0x0000046c
loc_478:
    478: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    47c: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    480: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    484: 01eba423  sw           x30, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    488: 01dba623  sw           x29, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    48c: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    490: 014baa23  sw           x20, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    494: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    498: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    49c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    4a0: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    4a4: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    4a8: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4ac: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    4b0: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    4b4: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    4b8: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    4bc: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    4c0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    4c4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    4c8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    4cc: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_4d0:
    4d0: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    4d4: 000b0463  beq          x22, x0, 0x000004dc  # target 0x000004dc
    4d8: ff9ff06f  jal          x0, 0x000004d0  # target 0x000004d0
loc_4dc:
    4dc: 00008067  jalr         x0, 0(x1)
loc_4e0:
    4e0: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    4e4: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b; 0x0000078c
    4e8: 007a7d13  andi         x26, x20, 7
    4ec: ff8a7a13  andi         x20, x20, -8
    4f0: 01af8ab3  add          x21, x31, x26
    4f4: 007afb93  andi         x23, x21, 7
    4f8: 003ada93  srli         x21, x21, 3
    4fc: 00ba9a93  slli         x21, x21, 11
    500: 014a8ab3  add          x21, x21, x20
    504: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000504
    508: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000051c
    50c: 001b9b93  slli         x23, x23, 1
    510: 017b0b33  add          x22, x22, x23
    514: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    518: 00008067  jalr         x0, 0(x1)
    51c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    520: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    524: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    528: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_52c:
    52c: 00000a17  auipc        x20, 0x00000  # x20 = 0x0000052c
    530: 0e0a0a13  addi         x20, x20, 224  # x20 = 0x0000060c
loc_534:
    534: 001f1a93  slli         x21, x30, 1
    538: 014a8ab3  add          x21, x21, x20
    53c: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_540:
    540: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    544: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb30244 · noc1_regs + 0x244
    548: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x244 · 0xffb30244
    54c: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    550: 018be463  bltu         x23, x24, 0x00000558  # target 0x00000558
    554: fedff06f  jal          x0, 0x00000540  # target 0x00000540
loc_558:
    558: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    55c: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb30148 · noc1_regs + 0x148
    560: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x148 · 0xffb30148
    564: 014b9b93  slli         x23, x23, 20
    568: 014bdb93  srli         x23, x23, 20
    56c: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
loc_570:
    570: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    574: 000c8463  beq          x25, x0, 0x0000057c  # target 0x0000057c
    578: ff9ff06f  jal          x0, 0x00000570  # target 0x00000570
loc_57c:
    57c: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    580: 01fd2023  sw           x31, 0(x26)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    584: 000d2223  sw           x0, 4(x26)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    588: 015d2423  sw           x21, 8(x26)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    58c: 01dd2623  sw           x29, 12(x26)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    590: 000d2823  sw           x0, 16(x26)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    594: 017d2a23  sw           x23, 20(x26)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    598: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    59c: 01bd2c23  sw           x27, 24(x26)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    5a0: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    5a4: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    5a8: 01bd2e23  sw           x27, 28(x26)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    5ac: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5b0: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    5b4: 03bd2023  sw           x27, 32(x26)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    5b8: 020d2223  sw           x0, 36(x26)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    5bc: 020d2423  sw           x0, 40(x26)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    5c0: 020d2623  sw           x0, 44(x26)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    5c4: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    5c8: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb30040 · noc1_regs + 0x40
    5cc: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    5d0: 01bd2023  sw           x27, 0(x26)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_5d4:
    5d4: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    5d8: 000c8463  beq          x25, x0, 0x000005e0  # target 0x000005e0
    5dc: ff9ff06f  jal          x0, 0x000005d4  # target 0x000005d4
loc_5e0:
    5e0: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5e4: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    5e8: 016e8eb3  add          x29, x29, x22
    5ec: 001f0f13  addi         x30, x30, 1
    5f0: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    5f4: 015f1663  bne          x30, x21, 0x00000600  # target 0x00000600
    5f8: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    5fc: 016f8fb3  add          x31, x31, x22
loc_600:
    600: fffe0e13  addi         x28, x28, -1
    604: f20e18e3  bne          x28, x0, 0x00000534  # target 0x00000534
    608: 00008067  jalr         x0, 0(x1)
    60c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    610: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    614: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    618: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    61c:           j FW_BRISC+4   # return to firmware, linked at install
