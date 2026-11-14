# llama3 8b-fp8 decode: down, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (48): 1,4 2,4 3,4 4,4 5,4 6,4 1,5 2,5 3,5 4,5 5,5 6,5 1,6 2,6 3,6 4,6 5,6 6,6 1,7 2,7 3,7 4,7 5,7 6,7 1,8 2,8 3,8 4,8 5,8 6,8 1,9 2,9 3,9 4,9 5,9 6,9 1,10 2,10 3,10 4,10 5,10 6,10 1,11 2,11 3,11 4,11 5,11 6,11
# params: 0x780=e2e_hidden_dense_decode_token, 0x784=e2e_l0_down, 0x788=input_scale_0, 0x78c=input_scale_1, 0x790=output_scale_0_0, 0x794=output_scale_0_1, 0x798=e2e_x_a, 0x79c=e2e_x_b, 0x11980=e2e_q_compact, 0x11984=e2e_l0_down_row_start, 0x11988=dense_start, 0x1198c=e2e_l0_down_rows
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 0004f2b7  lui          x5, 0x0004f  # x5 = 0x0004f000
      c: 08028293  addi         x5, x5, 128  # x5 = 0x0004f080
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0004f080
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     24: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     28: 00012537  lui          x10, 0x00012  # x10 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     2c: 08050513  addi         x10, x10, 128  # x10 = 0x00012080
     30: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00012080
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
     64: 00e00393  addi         x7, x0, 14  # x7 = 0x0000000e
     68: 406383b3  sub          x7, x7, x6
     6c: 00e00413  addi         x8, x0, 14  # x8 = 0x0000000e
     70: 0083f663  bgeu         x7, x8, 0x0000007c  # target 0x0000007c
     74: 0ff0000f  fence        0xf, 0xf
     78: fd5ff06f  jal          x0, 0x0000004c  # target 0x0000004c
loc_7c:
     7c: 0ff0000f  fence        0xf, 0xf
     80: 430000ef  jal          x1, 0x000004b0  # target 0x000004b0; x1 = 0x00000084
     84: 448000ef  jal          x1, 0x000004cc  # target 0x000004cc; x1 = 0x00000088
     88: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     8c: 45c000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 0004feb7  lui          x29, 0x0004f  # x29 = 0x0004f000
     a4: 080e8e93  addi         x29, x29, 128  # x29 = 0x0004f080
     a8: 48c000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x000000ac
     ac: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     b0: 438000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 00050eb7  lui          x29, 0x00050  # x29 = 0x00050000 · arc_apb_niu0 + 0x0
     c8: 880e8e93  addi         x29, x29, -1920  # x29 = 0x0004f880
     cc: 468000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x000000d0
     d0: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     d4: 414000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x000000d8
     d8: 000a8213  addi         x4, x21, 0
     dc: 000b0293  addi         x5, x22, 0
     e0: 00020f93  addi         x31, x4, 0
     e4: 00028f13  addi         x30, x5, 0
     e8: 00050eb7  lui          x29, 0x00050  # x29 = 0x00050000 · arc_apb_niu0 + 0x0
     ec: 080e8e93  addi         x29, x29, 128  # x29 = 0x00050080 · arc_apb_niu0 + 0x80
     f0: 444000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x000000f4
     f4: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     f8: 3f0000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x000000fc
     fc: 000a8213  addi         x4, x21, 0
    100: 000b0293  addi         x5, x22, 0
    104: 00020f93  addi         x31, x4, 0
    108: 00028f13  addi         x30, x5, 0
    10c: 00051eb7  lui          x29, 0x00051  # x29 = 0x00051000
    110: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00050880 · arc_apb_niu0 + 0x880
    114: 420000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x00000118
    118: 00400f93  addi         x31, x0, 4  # x31 = 0x00000004
    11c: 3cc000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x00000120
    120: 000a8213  addi         x4, x21, 0
    124: 000b0293  addi         x5, x22, 0
    128: 00020f93  addi         x31, x4, 0
    12c: 00028f13  addi         x30, x5, 0
    130: 00051eb7  lui          x29, 0x00051  # x29 = 0x00051000
    134: 080e8e93  addi         x29, x29, 128  # x29 = 0x00051080
    138: 3fc000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x0000013c
    13c: 00500f93  addi         x31, x0, 5  # x31 = 0x00000005
    140: 3a8000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x00000144
    144: 000a8213  addi         x4, x21, 0
    148: 000b0293  addi         x5, x22, 0
    14c: 00020f93  addi         x31, x4, 0
    150: 00028f13  addi         x30, x5, 0
    154: 00052eb7  lui          x29, 0x00052  # x29 = 0x00052000
    158: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00051880
    15c: 3d8000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x00000160
    160: 00600f93  addi         x31, x0, 6  # x31 = 0x00000006
    164: 384000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x00000168
    168: 000a8213  addi         x4, x21, 0
    16c: 000b0293  addi         x5, x22, 0
    170: 00020f93  addi         x31, x4, 0
    174: 00028f13  addi         x30, x5, 0
    178: 00052eb7  lui          x29, 0x00052  # x29 = 0x00052000
    17c: 080e8e93  addi         x29, x29, 128  # x29 = 0x00052080
    180: 3b4000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x00000184
    184: 00700f93  addi         x31, x0, 7  # x31 = 0x00000007
    188: 360000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x0000018c
    18c: 000a8213  addi         x4, x21, 0
    190: 000b0293  addi         x5, x22, 0
    194: 00020f93  addi         x31, x4, 0
    198: 00028f13  addi         x30, x5, 0
    19c: 00053eb7  lui          x29, 0x00053  # x29 = 0x00053000
    1a0: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00052880
    1a4: 390000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x000001a8
    1a8: 00800f93  addi         x31, x0, 8  # x31 = 0x00000008
    1ac: 33c000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x000001b0
    1b0: 000a8213  addi         x4, x21, 0
    1b4: 000b0293  addi         x5, x22, 0
    1b8: 00020f93  addi         x31, x4, 0
    1bc: 00028f13  addi         x30, x5, 0
    1c0: 00053eb7  lui          x29, 0x00053  # x29 = 0x00053000
    1c4: 080e8e93  addi         x29, x29, 128  # x29 = 0x00053080
    1c8: 36c000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x000001cc
    1cc: 00900f93  addi         x31, x0, 9  # x31 = 0x00000009
    1d0: 318000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x000001d4
    1d4: 000a8213  addi         x4, x21, 0
    1d8: 000b0293  addi         x5, x22, 0
    1dc: 00020f93  addi         x31, x4, 0
    1e0: 00028f13  addi         x30, x5, 0
    1e4: 00054eb7  lui          x29, 0x00054  # x29 = 0x00054000
    1e8: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00053880
    1ec: 348000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x000001f0
    1f0: 00a00f93  addi         x31, x0, 10  # x31 = 0x0000000a
    1f4: 2f4000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x000001f8
    1f8: 000a8213  addi         x4, x21, 0
    1fc: 000b0293  addi         x5, x22, 0
    200: 00020f93  addi         x31, x4, 0
    204: 00028f13  addi         x30, x5, 0
    208: 00054eb7  lui          x29, 0x00054  # x29 = 0x00054000
    20c: 080e8e93  addi         x29, x29, 128  # x29 = 0x00054080
    210: 324000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x00000214
    214: 00b00f93  addi         x31, x0, 11  # x31 = 0x0000000b
    218: 2d0000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x0000021c
    21c: 000a8213  addi         x4, x21, 0
    220: 000b0293  addi         x5, x22, 0
    224: 00020f93  addi         x31, x4, 0
    228: 00028f13  addi         x30, x5, 0
    22c: 00055eb7  lui          x29, 0x00055  # x29 = 0x00055000
    230: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00054880
    234: 300000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x00000238
    238: 00c00f93  addi         x31, x0, 12  # x31 = 0x0000000c
    23c: 2ac000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x00000240
    240: 000a8213  addi         x4, x21, 0
    244: 000b0293  addi         x5, x22, 0
    248: 00020f93  addi         x31, x4, 0
    24c: 00028f13  addi         x30, x5, 0
    250: 00055eb7  lui          x29, 0x00055  # x29 = 0x00055000
    254: 080e8e93  addi         x29, x29, 128  # x29 = 0x00055080
    258: 2dc000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x0000025c
    25c: 00d00f93  addi         x31, x0, 13  # x31 = 0x0000000d
    260: 288000ef  jal          x1, 0x000004e8  # target 0x000004e8; x1 = 0x00000264
    264: 000a8213  addi         x4, x21, 0
    268: 000b0293  addi         x5, x22, 0
    26c: 00020f93  addi         x31, x4, 0
    270: 00028f13  addi         x30, x5, 0
    274: 00056eb7  lui          x29, 0x00056  # x29 = 0x00056000
    278: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00055880
    27c: 2b8000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x00000280
    280: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    284: 354000ef  jal          x1, 0x000005d8  # target 0x000005d8; x1 = 0x00000288
    288: 000a8213  addi         x4, x21, 0
    28c: 000b0293  addi         x5, x22, 0
    290: 00020f93  addi         x31, x4, 0
    294: 00028f13  addi         x30, x5, 0
    298: 00056eb7  lui          x29, 0x00056  # x29 = 0x00056000
    29c: 080e8e93  addi         x29, x29, 128  # x29 = 0x00056080
    2a0: 294000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x000002a4
    2a4: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    2a8: 330000ef  jal          x1, 0x000005d8  # target 0x000005d8; x1 = 0x000002ac
    2ac: 000a8213  addi         x4, x21, 0
    2b0: 000b0293  addi         x5, x22, 0
    2b4: 00020f93  addi         x31, x4, 0
    2b8: 00028f13  addi         x30, x5, 0
    2bc: 00057eb7  lui          x29, 0x00057  # x29 = 0x00057000
    2c0: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00056880
    2c4: 270000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x000002c8
    2c8: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    2cc: 30c000ef  jal          x1, 0x000005d8  # target 0x000005d8; x1 = 0x000002d0
    2d0: 000a8213  addi         x4, x21, 0
    2d4: 000b0293  addi         x5, x22, 0
    2d8: 00020f93  addi         x31, x4, 0
    2dc: 00028f13  addi         x30, x5, 0
    2e0: 00057eb7  lui          x29, 0x00057  # x29 = 0x00057000
    2e4: 080e8e93  addi         x29, x29, 128  # x29 = 0x00057080
    2e8: 24c000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x000002ec
    2ec: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    2f0: 2e8000ef  jal          x1, 0x000005d8  # target 0x000005d8; x1 = 0x000002f4
    2f4: 000a8213  addi         x4, x21, 0
    2f8: 000b0293  addi         x5, x22, 0
    2fc: 00020f93  addi         x31, x4, 0
    300: 00028f13  addi         x30, x5, 0
    304: 00058eb7  lui          x29, 0x00058  # x29 = 0x00058000 · arc_apb_niu1 + 0x0
    308: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00057880
    30c: 228000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x00000310
    310: 1bc000ef  jal          x1, 0x000004cc  # target 0x000004cc; x1 = 0x00000314
    314: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    318: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    31c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    320: 000072b7  lui          x5, 0x00007  # x5 = 0x00007000
    324: 00520233  add          x4, x4, x5
    328: 00056337  lui          x6, 0x00056  # x6 = 0x00056000
    32c: 08030313  addi         x6, x6, 128  # x6 = 0x00056080
    330: 00626663  bltu         x4, x6, 0x0000033c  # target 0x0000033c
    334: 000073b7  lui          x7, 0x00007  # x7 = 0x00007000
    338: 40720233  sub          x4, x4, x7
loc_33c:
    33c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    340: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    344: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    348: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    34c: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    350: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    354: 00e20213  addi         x4, x4, 14
    358: 01021213  slli         x4, x4, 16
    35c: 01025213  srli         x4, x4, 16
    360: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    364: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    368: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    36c: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    370: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    374: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    378: 0ff0000f  fence        0xf, 0xf
    37c: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    380: 98c28293  addi         x5, x5, -1652  # x5 = 0x0001198c
    384: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0001198c
    388: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    38c: 0003a283  lw           x5, 0(x7)  # param e2e_l0_down; 0x00000784
    390: ff82f293  andi         x5, x5, -8
    394: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    398: 98448493  addi         x9, x9, -1660  # x9 = 0x00011984
    39c: 0004a383  lw           x7, 0(x9)  # param e2e_l0_down_row_start; 0x00011984
    3a0: 00700413  addi         x8, x0, 7  # x8 = 0x00000007
    3a4: 028383b3  mul          x7, x7, x8
    3a8: 0073f313  andi         x6, x7, 7
    3ac: 0033d393  srli         x7, x7, 3
    3b0: 00b39393  slli         x7, x7, 11
    3b4: 007282b3  add          x5, x5, x7
    3b8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    3bc: 00020413  addi         x8, x4, 0
loc_3c0:
    3c0: 0e83f663  bgeu         x7, x8, 0x000004ac  # target 0x000004ac
    3c4: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    3c8: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    3cc: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_3d0:
    3d0: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    3d4: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    3d8: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    3dc: 40a485b3  sub          x11, x9, x10
    3e0: 01059593  slli         x11, x11, 16
    3e4: 0105d593  srli         x11, x11, 16
    3e8: 0e000613  addi         x12, x0, 224  # x12 = 0x000000e0
    3ec: 40b60633  sub          x12, x12, x11
    3f0: 00e00693  addi         x13, x0, 14  # x13 = 0x0000000e
    3f4: 00d67663  bgeu         x12, x13, 0x00000400  # target 0x00000400
    3f8: 0ff0000f  fence        0xf, 0xf
    3fc: fd5ff06f  jal          x0, 0x000003d0  # target 0x000003d0
loc_400:
    400: 0ff0000f  fence        0xf, 0xf
    404: 0ac000ef  jal          x1, 0x000004b0  # target 0x000004b0; x1 = 0x00000408
    408: 0c4000ef  jal          x1, 0x000004cc  # target 0x000004cc; x1 = 0x0000040c
    40c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    410: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    414: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    418: 00028f93  addi         x31, x5, 0
    41c: 00030f13  addi         x30, x6, 0
    420: 00048e93  addi         x29, x9, 0
    424: 00700e13  addi         x28, x0, 7  # x28 = 0x00000007
    428: 1fc000ef  jal          x1, 0x00000624  # target 0x00000624; x1 = 0x0000042c
    42c: 000f8293  addi         x5, x31, 0
    430: 000f0313  addi         x6, x30, 0
    434: 098000ef  jal          x1, 0x000004cc  # target 0x000004cc; x1 = 0x00000438
    438: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    43c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    440: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    444: 00004537  lui          x10, 0x00004  # x10 = 0x00004000
    448: 80050513  addi         x10, x10, -2048  # x10 = 0x00003800
    44c: 00a484b3  add          x9, x9, x10
    450: 0004a5b7  lui          x11, 0x0004a  # x11 = 0x0004a000
    454: 08058593  addi         x11, x11, 128  # x11 = 0x0004a080
    458: 00b4e663  bltu         x9, x11, 0x00000464  # target 0x00000464
    45c: 00038637  lui          x12, 0x00038  # x12 = 0x00038000 · arc_apb_reset_unit + 0x8000
    460: 40c484b3  sub          x9, x9, x12
loc_464:
    464: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    468: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    46c: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    470: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    474: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    478: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    47c: 00e48493  addi         x9, x9, 14
    480: 01049493  slli         x9, x9, 16
    484: 0104d493  srli         x9, x9, 16
    488: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    48c: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    490: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    494: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    498: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    49c: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    4a0: 0ff0000f  fence        0xf, 0xf
    4a4: 00138393  addi         x7, x7, 1
    4a8: f19ff06f  jal          x0, 0x000003c0  # target 0x000003c0
loc_4ac:
    4ac: 2680006f  jal          x0, 0x00000714  # target 0x00000714
loc_4b0:
    4b0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4b4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    4b8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    4bc: 000a0463  beq          x20, x0, 0x000004c4  # target 0x000004c4
    4c0: ff1ff06f  jal          x0, 0x000004b0  # target 0x000004b0
loc_4c4:
    4c4: 0ff0000f  fence        0xf, 0xf
    4c8: 00008067  jalr         x0, 0(x1)
loc_4cc:
    4cc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4d0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    4d4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    4d8: 000a0463  beq          x20, x0, 0x000004e0  # target 0x000004e0
    4dc: ff1ff06f  jal          x0, 0x000004cc  # target 0x000004cc
loc_4e0:
    4e0: 0ff0000f  fence        0xf, 0xf
    4e4: 00008067  jalr         x0, 0(x1)
loc_4e8:
    4e8: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    4ec: 000aaa03  lw           x20, 0(x21)  # param e2e_hidden_dense_decode_token; 0x00000780
    4f0: 007a7d13  andi         x26, x20, 7
    4f4: ff8a7a13  andi         x20, x20, -8
    4f8: 01af8ab3  add          x21, x31, x26
    4fc: 007afb93  andi         x23, x21, 7
    500: 003ada93  srli         x21, x21, 3
    504: 00ba9a93  slli         x21, x21, 11
    508: 014a8ab3  add          x21, x21, x20
    50c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000050c
    510: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000524
    514: 001b9b93  slli         x23, x23, 1
    518: 017b0b33  add          x22, x22, x23
    51c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    520: 00008067  jalr         x0, 0(x1)
    524: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    528: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    52c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    530: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_534:
    534: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    538: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    53c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    540: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    544: 015a6463  bltu         x20, x21, 0x0000054c  # target 0x0000054c
    548: fedff06f  jal          x0, 0x00000534  # target 0x00000534
loc_54c:
    54c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    550: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    554: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    558: 014a1a13  slli         x20, x20, 20
    55c: 014a5a13  srli         x20, x20, 20
    560: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_564:
    564: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    568: 000b0463  beq          x22, x0, 0x00000570  # target 0x00000570
    56c: ff9ff06f  jal          x0, 0x00000564  # target 0x00000564
loc_570:
    570: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    574: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    578: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    57c: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    580: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    584: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    588: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    58c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    590: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    594: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    598: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    59c: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    5a0: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5a4: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    5a8: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    5ac: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    5b0: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    5b4: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    5b8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    5bc: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    5c0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    5c4: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_5c8:
    5c8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5cc: 000b0463  beq          x22, x0, 0x000005d4  # target 0x000005d4
    5d0: ff9ff06f  jal          x0, 0x000005c8  # target 0x000005c8
loc_5d4:
    5d4: 00008067  jalr         x0, 0(x1)
loc_5d8:
    5d8: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    5dc: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b; 0x0000079c
    5e0: 007a7d13  andi         x26, x20, 7
    5e4: ff8a7a13  andi         x20, x20, -8
    5e8: 01af8ab3  add          x21, x31, x26
    5ec: 007afb93  andi         x23, x21, 7
    5f0: 003ada93  srli         x21, x21, 3
    5f4: 00ba9a93  slli         x21, x21, 11
    5f8: 014a8ab3  add          x21, x21, x20
    5fc: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005fc
    600: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000614
    604: 001b9b93  slli         x23, x23, 1
    608: 017b0b33  add          x22, x22, x23
    60c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    610: 00008067  jalr         x0, 0(x1)
    614: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    618: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    61c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    620: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_624:
    624: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000624
    628: 0e0a0a13  addi         x20, x20, 224  # x20 = 0x00000704
loc_62c:
    62c: 001f1a93  slli         x21, x30, 1
    630: 014a8ab3  add          x21, x21, x20
    634: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_638:
    638: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    63c: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    640: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    644: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    648: 018be463  bltu         x23, x24, 0x00000650  # target 0x00000650
    64c: fedff06f  jal          x0, 0x00000638  # target 0x00000638
loc_650:
    650: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    654: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    658: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    65c: 014b9b93  slli         x23, x23, 20
    660: 014bdb93  srli         x23, x23, 20
    664: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_668:
    668: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    66c: 000c8463  beq          x25, x0, 0x00000674  # target 0x00000674
    670: ff9ff06f  jal          x0, 0x00000668  # target 0x00000668
loc_674:
    674: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    678: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    67c: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    680: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    684: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    688: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    68c: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    690: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    694: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    698: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    69c: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    6a0: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    6a4: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6a8: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    6ac: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    6b0: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    6b4: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    6b8: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    6bc: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    6c0: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    6c4: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    6c8: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_6cc:
    6cc: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    6d0: 000c8463  beq          x25, x0, 0x000006d8  # target 0x000006d8
    6d4: ff9ff06f  jal          x0, 0x000006cc  # target 0x000006cc
loc_6d8:
    6d8: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6dc: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    6e0: 016e8eb3  add          x29, x29, x22
    6e4: 001f0f13  addi         x30, x30, 1
    6e8: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    6ec: 015f1663  bne          x30, x21, 0x000006f8  # target 0x000006f8
    6f0: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    6f4: 016f8fb3  add          x31, x31, x22
loc_6f8:
    6f8: fffe0e13  addi         x28, x28, -1
    6fc: f20e18e3  bne          x28, x0, 0x0000062c  # target 0x0000062c
    700: 00008067  jalr         x0, 0(x1)
    704: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    708: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    70c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    710: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    714:           j FW_BRISC+4   # return to firmware, linked at install
