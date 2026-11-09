# llama3 8b-fp8 decode: down, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (48): 7,4 10,4 11,4 12,4 13,4 14,4 7,5 10,5 11,5 12,5 13,5 14,5 7,6 10,6 11,6 12,6 13,6 14,6 7,7 10,7 11,7 12,7 13,7 14,7 7,8 10,8 11,8 12,8 13,8 14,8 7,9 10,9 11,9 12,9 13,9 14,9 7,10 10,10 11,10 12,10 13,10 14,10 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x7c0=e2e_hidden_dense_decode_token, 0x7c4=e2e_l0_down, 0x7c8=input_scale_0, 0x7cc=input_scale_1, 0x7d0=output_scale_0_0, 0x7d4=output_scale_0_1, 0x7d8=e2e_x_a, 0x7dc=e2e_x_b, 0x8140=e2e_q_compact, 0x8144=e2e_l0_down_row_start, 0x8148=dense_start, 0x814c=e2e_l0_down_rows
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000cd2b7  lui          x5, 0x000cd  # x5 = 0x000cd000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x000cd000
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
     5c: 00e00393  addi         x7, x0, 14  # x7 = 0x0000000e
     60: 406383b3  sub          x7, x7, x6
     64: 00e00413  addi         x8, x0, 14  # x8 = 0x0000000e
     68: 0083f663  bgeu         x7, x8, 0x00000074  # target 0x00000074
     6c: 0ff0000f  fence        0xf, 0xf
     70: fd5ff06f  jal          x0, 0x00000044  # target 0x00000044
loc_74:
     74: 0ff0000f  fence        0xf, 0xf
     78: 404000ef  jal          x1, 0x0000047c  # target 0x0000047c; x1 = 0x0000007c
     7c: 41c000ef  jal          x1, 0x00000498  # target 0x00000498; x1 = 0x00000080
     80: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     84: 430000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x00000088
     88: 000a8213  addi         x4, x21, 0
     8c: 000b0293  addi         x5, x22, 0
     90: 00020f93  addi         x31, x4, 0
     94: 00028f13  addi         x30, x5, 0
     98: 000cdeb7  lui          x29, 0x000cd  # x29 = 0x000cd000
     9c: 464000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x000000a0
     a0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     a4: 410000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x000000a8
     a8: 000a8213  addi         x4, x21, 0
     ac: 000b0293  addi         x5, x22, 0
     b0: 00020f93  addi         x31, x4, 0
     b4: 00028f13  addi         x30, x5, 0
     b8: 000ceeb7  lui          x29, 0x000ce  # x29 = 0x000ce000
     bc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000cd800
     c0: 440000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x000000c4
     c4: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     c8: 3ec000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x000000cc
     cc: 000a8213  addi         x4, x21, 0
     d0: 000b0293  addi         x5, x22, 0
     d4: 00020f93  addi         x31, x4, 0
     d8: 00028f13  addi         x30, x5, 0
     dc: 000ceeb7  lui          x29, 0x000ce  # x29 = 0x000ce000
     e0: 420000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x000000e4
     e4: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     e8: 3cc000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x000000ec
     ec: 000a8213  addi         x4, x21, 0
     f0: 000b0293  addi         x5, x22, 0
     f4: 00020f93  addi         x31, x4, 0
     f8: 00028f13  addi         x30, x5, 0
     fc: 000cfeb7  lui          x29, 0x000cf  # x29 = 0x000cf000
    100: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000ce800
    104: 3fc000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x00000108
    108: 00400f93  addi         x31, x0, 4  # x31 = 0x00000004
    10c: 3a8000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x00000110
    110: 000a8213  addi         x4, x21, 0
    114: 000b0293  addi         x5, x22, 0
    118: 00020f93  addi         x31, x4, 0
    11c: 00028f13  addi         x30, x5, 0
    120: 000cfeb7  lui          x29, 0x000cf  # x29 = 0x000cf000
    124: 3dc000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x00000128
    128: 00500f93  addi         x31, x0, 5  # x31 = 0x00000005
    12c: 388000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x00000130
    130: 000a8213  addi         x4, x21, 0
    134: 000b0293  addi         x5, x22, 0
    138: 00020f93  addi         x31, x4, 0
    13c: 00028f13  addi         x30, x5, 0
    140: 000d0eb7  lui          x29, 0x000d0  # x29 = 0x000d0000
    144: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000cf800
    148: 3b8000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x0000014c
    14c: 00600f93  addi         x31, x0, 6  # x31 = 0x00000006
    150: 364000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x00000154
    154: 000a8213  addi         x4, x21, 0
    158: 000b0293  addi         x5, x22, 0
    15c: 00020f93  addi         x31, x4, 0
    160: 00028f13  addi         x30, x5, 0
    164: 000d0eb7  lui          x29, 0x000d0  # x29 = 0x000d0000
    168: 398000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x0000016c
    16c: 00700f93  addi         x31, x0, 7  # x31 = 0x00000007
    170: 344000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x00000174
    174: 000a8213  addi         x4, x21, 0
    178: 000b0293  addi         x5, x22, 0
    17c: 00020f93  addi         x31, x4, 0
    180: 00028f13  addi         x30, x5, 0
    184: 000d1eb7  lui          x29, 0x000d1  # x29 = 0x000d1000
    188: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000d0800
    18c: 374000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x00000190
    190: 00800f93  addi         x31, x0, 8  # x31 = 0x00000008
    194: 320000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x00000198
    198: 000a8213  addi         x4, x21, 0
    19c: 000b0293  addi         x5, x22, 0
    1a0: 00020f93  addi         x31, x4, 0
    1a4: 00028f13  addi         x30, x5, 0
    1a8: 000d1eb7  lui          x29, 0x000d1  # x29 = 0x000d1000
    1ac: 354000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x000001b0
    1b0: 00900f93  addi         x31, x0, 9  # x31 = 0x00000009
    1b4: 300000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x000001b8
    1b8: 000a8213  addi         x4, x21, 0
    1bc: 000b0293  addi         x5, x22, 0
    1c0: 00020f93  addi         x31, x4, 0
    1c4: 00028f13  addi         x30, x5, 0
    1c8: 000d2eb7  lui          x29, 0x000d2  # x29 = 0x000d2000
    1cc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000d1800
    1d0: 330000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x000001d4
    1d4: 00a00f93  addi         x31, x0, 10  # x31 = 0x0000000a
    1d8: 2dc000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x000001dc
    1dc: 000a8213  addi         x4, x21, 0
    1e0: 000b0293  addi         x5, x22, 0
    1e4: 00020f93  addi         x31, x4, 0
    1e8: 00028f13  addi         x30, x5, 0
    1ec: 000d2eb7  lui          x29, 0x000d2  # x29 = 0x000d2000
    1f0: 310000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x000001f4
    1f4: 00b00f93  addi         x31, x0, 11  # x31 = 0x0000000b
    1f8: 2bc000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x000001fc
    1fc: 000a8213  addi         x4, x21, 0
    200: 000b0293  addi         x5, x22, 0
    204: 00020f93  addi         x31, x4, 0
    208: 00028f13  addi         x30, x5, 0
    20c: 000d3eb7  lui          x29, 0x000d3  # x29 = 0x000d3000
    210: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000d2800
    214: 2ec000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x00000218
    218: 00c00f93  addi         x31, x0, 12  # x31 = 0x0000000c
    21c: 298000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x00000220
    220: 000a8213  addi         x4, x21, 0
    224: 000b0293  addi         x5, x22, 0
    228: 00020f93  addi         x31, x4, 0
    22c: 00028f13  addi         x30, x5, 0
    230: 000d3eb7  lui          x29, 0x000d3  # x29 = 0x000d3000
    234: 2cc000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x00000238
    238: 00d00f93  addi         x31, x0, 13  # x31 = 0x0000000d
    23c: 278000ef  jal          x1, 0x000004b4  # target 0x000004b4; x1 = 0x00000240
    240: 000a8213  addi         x4, x21, 0
    244: 000b0293  addi         x5, x22, 0
    248: 00020f93  addi         x31, x4, 0
    24c: 00028f13  addi         x30, x5, 0
    250: 000d4eb7  lui          x29, 0x000d4  # x29 = 0x000d4000
    254: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000d3800
    258: 2a8000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x0000025c
    25c: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    260: 344000ef  jal          x1, 0x000005a4  # target 0x000005a4; x1 = 0x00000264
    264: 000a8213  addi         x4, x21, 0
    268: 000b0293  addi         x5, x22, 0
    26c: 00020f93  addi         x31, x4, 0
    270: 00028f13  addi         x30, x5, 0
    274: 000d4eb7  lui          x29, 0x000d4  # x29 = 0x000d4000
    278: 288000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x0000027c
    27c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    280: 324000ef  jal          x1, 0x000005a4  # target 0x000005a4; x1 = 0x00000284
    284: 000a8213  addi         x4, x21, 0
    288: 000b0293  addi         x5, x22, 0
    28c: 00020f93  addi         x31, x4, 0
    290: 00028f13  addi         x30, x5, 0
    294: 000d5eb7  lui          x29, 0x000d5  # x29 = 0x000d5000
    298: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000d4800
    29c: 264000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x000002a0
    2a0: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    2a4: 300000ef  jal          x1, 0x000005a4  # target 0x000005a4; x1 = 0x000002a8
    2a8: 000a8213  addi         x4, x21, 0
    2ac: 000b0293  addi         x5, x22, 0
    2b0: 00020f93  addi         x31, x4, 0
    2b4: 00028f13  addi         x30, x5, 0
    2b8: 000d5eb7  lui          x29, 0x000d5  # x29 = 0x000d5000
    2bc: 244000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x000002c0
    2c0: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    2c4: 2e0000ef  jal          x1, 0x000005a4  # target 0x000005a4; x1 = 0x000002c8
    2c8: 000a8213  addi         x4, x21, 0
    2cc: 000b0293  addi         x5, x22, 0
    2d0: 00020f93  addi         x31, x4, 0
    2d4: 00028f13  addi         x30, x5, 0
    2d8: 000d6eb7  lui          x29, 0x000d6  # x29 = 0x000d6000
    2dc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000d5800
    2e0: 220000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x000002e4
    2e4: 1b4000ef  jal          x1, 0x00000498  # target 0x00000498; x1 = 0x000002e8
    2e8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    2ec: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    2f0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    2f4: 000072b7  lui          x5, 0x00007  # x5 = 0x00007000
    2f8: 00520233  add          x4, x4, x5
    2fc: 000d4337  lui          x6, 0x000d4  # x6 = 0x000d4000
    300: 00626663  bltu         x4, x6, 0x0000030c  # target 0x0000030c
    304: 000073b7  lui          x7, 0x00007  # x7 = 0x00007000
    308: 40720233  sub          x4, x4, x7
loc_30c:
    30c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    310: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    314: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    318: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    31c: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    320: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    324: 00e20213  addi         x4, x4, 14
    328: 01021213  slli         x4, x4, 16
    32c: 01025213  srli         x4, x4, 16
    330: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    334: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    338: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    33c: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    340: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    344: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    348: 0ff0000f  fence        0xf, 0xf
    34c: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    350: 14c28293  addi         x5, x5, 332  # x5 = 0x0000814c
    354: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0000814c
    358: 7c400393  addi         x7, x0, 1988  # x7 = 0x000007c4
    35c: 0003a283  lw           x5, 0(x7)  # param e2e_l0_down; 0x000007c4
    360: ff82f293  andi         x5, x5, -8
    364: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    368: 14448493  addi         x9, x9, 324  # x9 = 0x00008144
    36c: 0004a383  lw           x7, 0(x9)  # param e2e_l0_down_row_start; 0x00008144
    370: 00700413  addi         x8, x0, 7  # x8 = 0x00000007
    374: 028383b3  mul          x7, x7, x8
    378: 0073f313  andi         x6, x7, 7
    37c: 0033d393  srli         x7, x7, 3
    380: 00b39393  slli         x7, x7, 11
    384: 007282b3  add          x5, x5, x7
    388: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    38c: 00020413  addi         x8, x4, 0
loc_390:
    390: 0e83f463  bgeu         x7, x8, 0x00000478  # target 0x00000478
    394: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    398: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    39c: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_3a0:
    3a0: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    3a4: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    3a8: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    3ac: 40a485b3  sub          x11, x9, x10
    3b0: 01059593  slli         x11, x11, 16
    3b4: 0105d593  srli         x11, x11, 16
    3b8: 0e000613  addi         x12, x0, 224  # x12 = 0x000000e0
    3bc: 40b60633  sub          x12, x12, x11
    3c0: 00e00693  addi         x13, x0, 14  # x13 = 0x0000000e
    3c4: 00d67663  bgeu         x12, x13, 0x000003d0  # target 0x000003d0
    3c8: 0ff0000f  fence        0xf, 0xf
    3cc: fd5ff06f  jal          x0, 0x000003a0  # target 0x000003a0
loc_3d0:
    3d0: 0ff0000f  fence        0xf, 0xf
    3d4: 0a8000ef  jal          x1, 0x0000047c  # target 0x0000047c; x1 = 0x000003d8
    3d8: 0c0000ef  jal          x1, 0x00000498  # target 0x00000498; x1 = 0x000003dc
    3dc: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3e0: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    3e4: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    3e8: 00028f93  addi         x31, x5, 0
    3ec: 00030f13  addi         x30, x6, 0
    3f0: 00048e93  addi         x29, x9, 0
    3f4: 00700e13  addi         x28, x0, 7  # x28 = 0x00000007
    3f8: 1f8000ef  jal          x1, 0x000005f0  # target 0x000005f0; x1 = 0x000003fc
    3fc: 000f8293  addi         x5, x31, 0
    400: 000f0313  addi         x6, x30, 0
    404: 094000ef  jal          x1, 0x00000498  # target 0x00000498; x1 = 0x00000408
    408: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    40c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    410: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    414: 00004537  lui          x10, 0x00004  # x10 = 0x00004000
    418: 80050513  addi         x10, x10, -2048  # x10 = 0x00003800
    41c: 00a484b3  add          x9, x9, x10
    420: 000c85b7  lui          x11, 0x000c8  # x11 = 0x000c8000
    424: 00b4e663  bltu         x9, x11, 0x00000430  # target 0x00000430
    428: 00038637  lui          x12, 0x00038  # x12 = 0x00038000 · arc_apb_reset_unit + 0x8000
    42c: 40c484b3  sub          x9, x9, x12
loc_430:
    430: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    434: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    438: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    43c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    440: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    444: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    448: 00e48493  addi         x9, x9, 14
    44c: 01049493  slli         x9, x9, 16
    450: 0104d493  srli         x9, x9, 16
    454: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    458: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    45c: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    460: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    464: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    468: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    46c: 0ff0000f  fence        0xf, 0xf
    470: 00138393  addi         x7, x7, 1
    474: f1dff06f  jal          x0, 0x00000390  # target 0x00000390
loc_478:
    478: 2680006f  jal          x0, 0x000006e0  # target 0x000006e0
loc_47c:
    47c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    480: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    484: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    488: 000a0463  beq          x20, x0, 0x00000490  # target 0x00000490
    48c: ff1ff06f  jal          x0, 0x0000047c  # target 0x0000047c
loc_490:
    490: 0ff0000f  fence        0xf, 0xf
    494: 00008067  jalr         x0, 0(x1)
loc_498:
    498: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    49c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    4a0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    4a4: 000a0463  beq          x20, x0, 0x000004ac  # target 0x000004ac
    4a8: ff1ff06f  jal          x0, 0x00000498  # target 0x00000498
loc_4ac:
    4ac: 0ff0000f  fence        0xf, 0xf
    4b0: 00008067  jalr         x0, 0(x1)
loc_4b4:
    4b4: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    4b8: 000aaa03  lw           x20, 0(x21)  # param e2e_hidden_dense_decode_token; 0x000007c0
    4bc: 007a7d13  andi         x26, x20, 7
    4c0: ff8a7a13  andi         x20, x20, -8
    4c4: 01af8ab3  add          x21, x31, x26
    4c8: 007afb93  andi         x23, x21, 7
    4cc: 003ada93  srli         x21, x21, 3
    4d0: 00ba9a93  slli         x21, x21, 11
    4d4: 014a8ab3  add          x21, x21, x20
    4d8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004d8
    4dc: 018b0b13  addi         x22, x22, 24  # x22 = 0x000004f0
    4e0: 001b9b93  slli         x23, x23, 1
    4e4: 017b0b33  add          x22, x22, x23
    4e8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4ec: 00008067  jalr         x0, 0(x1)
    4f0: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f4: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f8: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4fc: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_500:
    500: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    504: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    508: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    50c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    510: 015a6463  bltu         x20, x21, 0x00000518  # target 0x00000518
    514: fedff06f  jal          x0, 0x00000500  # target 0x00000500
loc_518:
    518: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    51c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    520: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    524: 014a1a13  slli         x20, x20, 20
    528: 014a5a13  srli         x20, x20, 20
    52c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_530:
    530: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    534: 000b0463  beq          x22, x0, 0x0000053c  # target 0x0000053c
    538: ff9ff06f  jal          x0, 0x00000530  # target 0x00000530
loc_53c:
    53c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    540: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    544: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    548: 01eba423  sw           x30, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    54c: 01dba623  sw           x29, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    550: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    554: 014baa23  sw           x20, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    558: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    55c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    560: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    564: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    568: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    56c: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    570: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    574: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    578: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    57c: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    580: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    584: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    588: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    58c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    590: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_594:
    594: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    598: 000b0463  beq          x22, x0, 0x000005a0  # target 0x000005a0
    59c: ff9ff06f  jal          x0, 0x00000594  # target 0x00000594
loc_5a0:
    5a0: 00008067  jalr         x0, 0(x1)
loc_5a4:
    5a4: 7dc00a93  addi         x21, x0, 2012  # x21 = 0x000007dc
    5a8: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b; 0x000007dc
    5ac: 007a7d13  andi         x26, x20, 7
    5b0: ff8a7a13  andi         x20, x20, -8
    5b4: 01af8ab3  add          x21, x31, x26
    5b8: 007afb93  andi         x23, x21, 7
    5bc: 003ada93  srli         x21, x21, 3
    5c0: 00ba9a93  slli         x21, x21, 11
    5c4: 014a8ab3  add          x21, x21, x20
    5c8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005c8
    5cc: 018b0b13  addi         x22, x22, 24  # x22 = 0x000005e0
    5d0: 001b9b93  slli         x23, x23, 1
    5d4: 017b0b33  add          x22, x22, x23
    5d8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    5dc: 00008067  jalr         x0, 0(x1)
    5e0: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5e4: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5e8: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    5ec: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_5f0:
    5f0: 00000a17  auipc        x20, 0x00000  # x20 = 0x000005f0
    5f4: 0e0a0a13  addi         x20, x20, 224  # x20 = 0x000006d0
loc_5f8:
    5f8: 001f1a93  slli         x21, x30, 1
    5fc: 014a8ab3  add          x21, x21, x20
    600: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_604:
    604: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    608: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb30244 · noc1_regs + 0x244
    60c: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x244 · 0xffb30244
    610: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    614: 018be463  bltu         x23, x24, 0x0000061c  # target 0x0000061c
    618: fedff06f  jal          x0, 0x00000604  # target 0x00000604
loc_61c:
    61c: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    620: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb30148 · noc1_regs + 0x148
    624: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x148 · 0xffb30148
    628: 014b9b93  slli         x23, x23, 20
    62c: 014bdb93  srli         x23, x23, 20
    630: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
loc_634:
    634: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    638: 000c8463  beq          x25, x0, 0x00000640  # target 0x00000640
    63c: ff9ff06f  jal          x0, 0x00000634  # target 0x00000634
loc_640:
    640: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    644: 01fd2023  sw           x31, 0(x26)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    648: 000d2223  sw           x0, 4(x26)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    64c: 015d2423  sw           x21, 8(x26)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    650: 01dd2623  sw           x29, 12(x26)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    654: 000d2823  sw           x0, 16(x26)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    658: 017d2a23  sw           x23, 20(x26)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    65c: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    660: 01bd2c23  sw           x27, 24(x26)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    664: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    668: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    66c: 01bd2e23  sw           x27, 28(x26)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    670: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    674: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    678: 03bd2023  sw           x27, 32(x26)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    67c: 020d2223  sw           x0, 36(x26)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    680: 020d2423  sw           x0, 40(x26)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    684: 020d2623  sw           x0, 44(x26)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    688: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    68c: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb30040 · noc1_regs + 0x40
    690: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    694: 01bd2023  sw           x27, 0(x26)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_698:
    698: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    69c: 000c8463  beq          x25, x0, 0x000006a4  # target 0x000006a4
    6a0: ff9ff06f  jal          x0, 0x00000698  # target 0x00000698
loc_6a4:
    6a4: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6a8: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    6ac: 016e8eb3  add          x29, x29, x22
    6b0: 001f0f13  addi         x30, x30, 1
    6b4: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    6b8: 015f1663  bne          x30, x21, 0x000006c4  # target 0x000006c4
    6bc: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    6c0: 016f8fb3  add          x31, x31, x22
loc_6c4:
    6c4: fffe0e13  addi         x28, x28, -1
    6c8: f20e18e3  bne          x28, x0, 0x000005f8  # target 0x000005f8
    6cc: 00008067  jalr         x0, 0(x1)
    6d0: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6d4: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6d8: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6dc: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    6e0:           j FW_BRISC+4   # return to firmware, linked at install
