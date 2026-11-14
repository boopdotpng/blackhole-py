# llama3 8b-bf16 decode: qkv, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_l0_q, 0x788=e2e_q, 0x78c=e2e_l0_k, 0x790=e2e_k, 0x794=e2e_l0_v, 0x798=e2e_v, 0x79c=e2e_l0_input_norm, 0x118c0=e2e_l0_q_row_start, 0x118c4=e2e_l0_k_row_start, 0x118c8=e2e_l0_v_row_start, 0x118cc=e2e_l0_q_rows, 0x118d0=e2e_l0_k_rows, 0x118d4=e2e_l0_v_rows, 0x118d8=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 86448493  addi         x9, x9, -1948  # x9 = 0xffb00864 · riscv_local_mem + 0x864
      8: 00016537  lui          x10, 0x00016  # x10 = 0x00016000
      c: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00016000
     10: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     14: 86848493  addi         x9, x9, -1944  # x9 = 0xffb00868 · riscv_local_mem + 0x868
     18: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     20: 8c030313  addi         x6, x6, -1856  # x6 = 0x000118c0
     24: 00032203  lw           x4, 0(x6)  # param e2e_l0_q_row_start; 0x000118c0
     28: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     2c: 8cc30313  addi         x6, x6, -1844  # x6 = 0x000118cc
     30: 00032283  lw           x5, 0(x6)  # param e2e_l0_q_rows; 0x000118cc
     34: 00121313  slli         x6, x4, 1
     38: 0001d3b7  lui          x7, 0x0001d  # x7 = 0x0001d000
     3c: 00730333  add          x6, x6, x7
     40: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
     44: 00028413  addi         x8, x5, 0
loc_48:
     48: 0c83f263  bgeu         x7, x8, 0x0000010c  # target 0x0000010c
     4c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
     50: 86868693  addi         x13, x13, -1944  # x13 = 0xffb00868 · riscv_local_mem + 0x868
     54: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x868 · 0xffb00868
     58: 00100613  addi         x12, x0, 1  # x12 = 0x00000001
loc_5c:
     5c: ffb496b7  lui          x13, 0xffb49  # x13 = 0xffb49000
     60: 02868693  addi         x13, x13, 40  # x13 = 0xffb49028
     64: 0006d503  lhu          x10, 0(x13)  # 0xffb49028
     68: 409505b3  sub          x11, x10, x9
     6c: 01059593  slli         x11, x11, 16
     70: 0105d593  srli         x11, x11, 16
     74: 00c5f663  bgeu         x11, x12, 0x00000080  # target 0x00000080
     78: 0ff0000f  fence        0xf, 0xf
     7c: fe1ff06f  jal          x0, 0x0000005c  # target 0x0000005c
loc_80:
     80: 0ff0000f  fence        0xf, 0xf
     84: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     88: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
     8c: 0005a483  lw           x9, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
     90: 0004d503  lhu          x10, 0(x9)  # Address depends on runtime register values
     94: 00a31023  sh           x10, 0(x6)  # Address depends on runtime register values
     98: 00230313  addi         x6, x6, 2
     9c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     a0: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
     a4: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
     a8: 00148493  addi         x9, x9, 1
     ac: 01049493  slli         x9, x9, 16
     b0: 0104d493  srli         x9, x9, 16
     b4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     b8: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
     bc: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
     c0: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
     c4: 02050513  addi         x10, x10, 32  # x10 = 0xffb49020
     c8: 00952023  sw           x9, 0(x10)  # 0xffb49020; write runtime value
     cc: 0ff0000f  fence        0xf, 0xf
     d0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
     d4: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
     d8: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864
     dc: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     e0: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
     e4: 00a484b3  add          x9, x9, x10
     e8: 000175b7  lui          x11, 0x00017  # x11 = 0x00017000
     ec: 00b4e663  bltu         x9, x11, 0x000000f8  # target 0x000000f8
     f0: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     f4: 40c484b3  sub          x9, x9, x12
loc_f8:
     f8: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
     fc: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
    100: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    104: 00138393  addi         x7, x7, 1
    108: f41ff06f  jal          x0, 0x00000048  # target 0x00000048
loc_10c:
    10c: 004282b3  add          x5, x5, x4
    110: 350000ef  jal          x1, 0x00000460  # target 0x00000460; x1 = 0x00000114
    114: 368000ef  jal          x1, 0x0000047c  # target 0x0000047c; x1 = 0x00000118
    118: 00020313  addi         x6, x4, 0
loc_11c:
    11c: 00a35393  srli         x7, x6, 10
    120: 00038f93  addi         x31, x7, 0
    124: 374000ef  jal          x1, 0x00000498  # target 0x00000498; x1 = 0x00000128
    128: 000a8693  addi         x13, x21, 0
    12c: 000b0713  addi         x14, x22, 0
    130: 00131413  slli         x8, x6, 1
    134: 0001d5b7  lui          x11, 0x0001d  # x11 = 0x0001d000
    138: 008585b3  add          x11, x11, x8
    13c: 7ff47413  andi         x8, x8, 2047
    140: 00868633  add          x12, x13, x8
    144: 00f37493  andi         x9, x6, 15
    148: 01000513  addi         x10, x0, 16  # x10 = 0x00000010
    14c: 409504b3  sub          x9, x10, x9
    150: 40628533  sub          x10, x5, x6
    154: 00957463  bgeu         x10, x9, 0x0000015c  # target 0x0000015c
    158: 00050493  addi         x9, x10, 0
loc_15c:
    15c: 00930333  add          x6, x6, x9
    160: 00149493  slli         x9, x9, 1
    164: 00058f93  addi         x31, x11, 0
    168: 00060f13  addi         x30, x12, 0
    16c: 00070e93  addi         x29, x14, 0
    170: 00048e13  addi         x28, x9, 0
    174: 3a8000ef  jal          x1, 0x0000051c  # target 0x0000051c; x1 = 0x00000178
    178: fa5362e3  bltu         x6, x5, 0x0000011c  # target 0x0000011c
    17c: 2e4000ef  jal          x1, 0x00000460  # target 0x00000460; x1 = 0x00000180
    180: 2fc000ef  jal          x1, 0x0000047c  # target 0x0000047c; x1 = 0x00000184
    184: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    188: 8c430313  addi         x6, x6, -1852  # x6 = 0x000118c4
    18c: 00032203  lw           x4, 0(x6)  # param e2e_l0_k_row_start; 0x000118c4
    190: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    194: 8d030313  addi         x6, x6, -1840  # x6 = 0x000118d0
    198: 00032283  lw           x5, 0(x6)  # param e2e_l0_k_rows; 0x000118d0
    19c: 00121313  slli         x6, x4, 1
    1a0: 0001f3b7  lui          x7, 0x0001f  # x7 = 0x0001f000
    1a4: 00730333  add          x6, x6, x7
    1a8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1ac: 00028413  addi         x8, x5, 0
loc_1b0:
    1b0: 0c83f263  bgeu         x7, x8, 0x00000274  # target 0x00000274
    1b4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    1b8: 86868693  addi         x13, x13, -1944  # x13 = 0xffb00868 · riscv_local_mem + 0x868
    1bc: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x868 · 0xffb00868
    1c0: 00100613  addi         x12, x0, 1  # x12 = 0x00000001
loc_1c4:
    1c4: ffb496b7  lui          x13, 0xffb49  # x13 = 0xffb49000
    1c8: 02868693  addi         x13, x13, 40  # x13 = 0xffb49028
    1cc: 0006d503  lhu          x10, 0(x13)  # 0xffb49028
    1d0: 409505b3  sub          x11, x10, x9
    1d4: 01059593  slli         x11, x11, 16
    1d8: 0105d593  srli         x11, x11, 16
    1dc: 00c5f663  bgeu         x11, x12, 0x000001e8  # target 0x000001e8
    1e0: 0ff0000f  fence        0xf, 0xf
    1e4: fe1ff06f  jal          x0, 0x000001c4  # target 0x000001c4
loc_1e8:
    1e8: 0ff0000f  fence        0xf, 0xf
    1ec: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1f0: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    1f4: 0005a483  lw           x9, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    1f8: 0004d503  lhu          x10, 0(x9)  # Address depends on runtime register values
    1fc: 00a31023  sh           x10, 0(x6)  # Address depends on runtime register values
    200: 00230313  addi         x6, x6, 2
    204: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    208: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
    20c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
    210: 00148493  addi         x9, x9, 1
    214: 01049493  slli         x9, x9, 16
    218: 0104d493  srli         x9, x9, 16
    21c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    220: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
    224: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    228: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
    22c: 02050513  addi         x10, x10, 32  # x10 = 0xffb49020
    230: 00952023  sw           x9, 0(x10)  # 0xffb49020; write runtime value
    234: 0ff0000f  fence        0xf, 0xf
    238: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    23c: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
    240: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864
    244: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    248: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    24c: 00a484b3  add          x9, x9, x10
    250: 000175b7  lui          x11, 0x00017  # x11 = 0x00017000
    254: 00b4e663  bltu         x9, x11, 0x00000260  # target 0x00000260
    258: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    25c: 40c484b3  sub          x9, x9, x12
loc_260:
    260: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    264: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
    268: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    26c: 00138393  addi         x7, x7, 1
    270: f41ff06f  jal          x0, 0x000001b0  # target 0x000001b0
loc_274:
    274: 004282b3  add          x5, x5, x4
    278: 1e8000ef  jal          x1, 0x00000460  # target 0x00000460; x1 = 0x0000027c
    27c: 200000ef  jal          x1, 0x0000047c  # target 0x0000047c; x1 = 0x00000280
    280: 00020313  addi         x6, x4, 0
loc_284:
    284: 00a35393  srli         x7, x6, 10
    288: 00038f93  addi         x31, x7, 0
    28c: 344000ef  jal          x1, 0x000005d0  # target 0x000005d0; x1 = 0x00000290
    290: 000a8693  addi         x13, x21, 0
    294: 000b0713  addi         x14, x22, 0
    298: 00131413  slli         x8, x6, 1
    29c: 0001f5b7  lui          x11, 0x0001f  # x11 = 0x0001f000
    2a0: 008585b3  add          x11, x11, x8
    2a4: 7ff47413  andi         x8, x8, 2047
    2a8: 00868633  add          x12, x13, x8
    2ac: 00f37493  andi         x9, x6, 15
    2b0: 01000513  addi         x10, x0, 16  # x10 = 0x00000010
    2b4: 409504b3  sub          x9, x10, x9
    2b8: 40628533  sub          x10, x5, x6
    2bc: 00957463  bgeu         x10, x9, 0x000002c4  # target 0x000002c4
    2c0: 00050493  addi         x9, x10, 0
loc_2c4:
    2c4: 00930333  add          x6, x6, x9
    2c8: 00149493  slli         x9, x9, 1
    2cc: 00058f93  addi         x31, x11, 0
    2d0: 00060f13  addi         x30, x12, 0
    2d4: 00070e93  addi         x29, x14, 0
    2d8: 00048e13  addi         x28, x9, 0
    2dc: 240000ef  jal          x1, 0x0000051c  # target 0x0000051c; x1 = 0x000002e0
    2e0: fa5362e3  bltu         x6, x5, 0x00000284  # target 0x00000284
    2e4: 17c000ef  jal          x1, 0x00000460  # target 0x00000460; x1 = 0x000002e8
    2e8: 194000ef  jal          x1, 0x0000047c  # target 0x0000047c; x1 = 0x000002ec
    2ec: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2f0: 8c830313  addi         x6, x6, -1848  # x6 = 0x000118c8
    2f4: 00032203  lw           x4, 0(x6)  # param e2e_l0_v_row_start; 0x000118c8
    2f8: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2fc: 8d430313  addi         x6, x6, -1836  # x6 = 0x000118d4
    300: 00032283  lw           x5, 0(x6)  # param e2e_l0_v_rows; 0x000118d4
    304: 00121313  slli         x6, x4, 1
    308: 000203b7  lui          x7, 0x00020  # x7 = 0x00020000
    30c: 80038393  addi         x7, x7, -2048  # x7 = 0x0001f800
    310: 00730333  add          x6, x6, x7
    314: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    318: 00028413  addi         x8, x5, 0
loc_31c:
    31c: 0c83f263  bgeu         x7, x8, 0x000003e0  # target 0x000003e0
    320: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    324: 86868693  addi         x13, x13, -1944  # x13 = 0xffb00868 · riscv_local_mem + 0x868
    328: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x868 · 0xffb00868
    32c: 00100613  addi         x12, x0, 1  # x12 = 0x00000001
loc_330:
    330: ffb496b7  lui          x13, 0xffb49  # x13 = 0xffb49000
    334: 02868693  addi         x13, x13, 40  # x13 = 0xffb49028
    338: 0006d503  lhu          x10, 0(x13)  # 0xffb49028
    33c: 409505b3  sub          x11, x10, x9
    340: 01059593  slli         x11, x11, 16
    344: 0105d593  srli         x11, x11, 16
    348: 00c5f663  bgeu         x11, x12, 0x00000354  # target 0x00000354
    34c: 0ff0000f  fence        0xf, 0xf
    350: fe1ff06f  jal          x0, 0x00000330  # target 0x00000330
loc_354:
    354: 0ff0000f  fence        0xf, 0xf
    358: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    35c: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    360: 0005a483  lw           x9, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    364: 0004d503  lhu          x10, 0(x9)  # Address depends on runtime register values
    368: 00a31023  sh           x10, 0(x6)  # Address depends on runtime register values
    36c: 00230313  addi         x6, x6, 2
    370: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    374: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
    378: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
    37c: 00148493  addi         x9, x9, 1
    380: 01049493  slli         x9, x9, 16
    384: 0104d493  srli         x9, x9, 16
    388: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    38c: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
    390: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    394: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
    398: 02050513  addi         x10, x10, 32  # x10 = 0xffb49020
    39c: 00952023  sw           x9, 0(x10)  # 0xffb49020; write runtime value
    3a0: 0ff0000f  fence        0xf, 0xf
    3a4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    3a8: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
    3ac: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864
    3b0: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3b4: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    3b8: 00a484b3  add          x9, x9, x10
    3bc: 000175b7  lui          x11, 0x00017  # x11 = 0x00017000
    3c0: 00b4e663  bltu         x9, x11, 0x000003cc  # target 0x000003cc
    3c4: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3c8: 40c484b3  sub          x9, x9, x12
loc_3cc:
    3cc: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    3d0: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
    3d4: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    3d8: 00138393  addi         x7, x7, 1
    3dc: f41ff06f  jal          x0, 0x0000031c  # target 0x0000031c
loc_3e0:
    3e0: 004282b3  add          x5, x5, x4
    3e4: 07c000ef  jal          x1, 0x00000460  # target 0x00000460; x1 = 0x000003e8
    3e8: 094000ef  jal          x1, 0x0000047c  # target 0x0000047c; x1 = 0x000003ec
    3ec: 00020313  addi         x6, x4, 0
loc_3f0:
    3f0: 00a35393  srli         x7, x6, 10
    3f4: 00038f93  addi         x31, x7, 0
    3f8: 25c000ef  jal          x1, 0x00000654  # target 0x00000654; x1 = 0x000003fc
    3fc: 000a8693  addi         x13, x21, 0
    400: 000b0713  addi         x14, x22, 0
    404: 00131413  slli         x8, x6, 1
    408: 000205b7  lui          x11, 0x00020  # x11 = 0x00020000
    40c: 80058593  addi         x11, x11, -2048  # x11 = 0x0001f800
    410: 008585b3  add          x11, x11, x8
    414: 7ff47413  andi         x8, x8, 2047
    418: 00868633  add          x12, x13, x8
    41c: 00f37493  andi         x9, x6, 15
    420: 01000513  addi         x10, x0, 16  # x10 = 0x00000010
    424: 409504b3  sub          x9, x10, x9
    428: 40628533  sub          x10, x5, x6
    42c: 00957463  bgeu         x10, x9, 0x00000434  # target 0x00000434
    430: 00050493  addi         x9, x10, 0
loc_434:
    434: 00930333  add          x6, x6, x9
    438: 00149493  slli         x9, x9, 1
    43c: 00058f93  addi         x31, x11, 0
    440: 00060f13  addi         x30, x12, 0
    444: 00070e93  addi         x29, x14, 0
    448: 00048e13  addi         x28, x9, 0
    44c: 0d0000ef  jal          x1, 0x0000051c  # target 0x0000051c; x1 = 0x00000450
    450: fa5360e3  bltu         x6, x5, 0x000003f0  # target 0x000003f0
    454: 00c000ef  jal          x1, 0x00000460  # target 0x00000460; x1 = 0x00000458
    458: 024000ef  jal          x1, 0x0000047c  # target 0x0000047c; x1 = 0x0000045c
    45c: 27c0006f  jal          x0, 0x000006d8  # target 0x000006d8
loc_460:
    460: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    464: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    468: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    46c: 000a0463  beq          x20, x0, 0x00000474  # target 0x00000474
    470: ff1ff06f  jal          x0, 0x00000460  # target 0x00000460
loc_474:
    474: 0ff0000f  fence        0xf, 0xf
    478: 00008067  jalr         x0, 0(x1)
loc_47c:
    47c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    480: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    484: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    488: 000a0463  beq          x20, x0, 0x00000490  # target 0x00000490
    48c: ff1ff06f  jal          x0, 0x0000047c  # target 0x0000047c
loc_490:
    490: 0ff0000f  fence        0xf, 0xf
    494: 00008067  jalr         x0, 0(x1)
loc_498:
    498: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    49c: 000aaa03  lw           x20, 0(x21)  # param e2e_q; 0x00000788
    4a0: 007a7d13  andi         x26, x20, 7
    4a4: ff8a7a13  andi         x20, x20, -8
    4a8: 01af8ab3  add          x21, x31, x26
    4ac: 007afb93  andi         x23, x21, 7
    4b0: 003ada93  srli         x21, x21, 3
    4b4: 00ba9a93  slli         x21, x21, 11
    4b8: 014a8ab3  add          x21, x21, x20
    4bc: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004bc
    4c0: 030b0b13  addi         x22, x22, 48  # x22 = 0x000004ec
    4c4: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    4c8: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    4cc: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
    4d0: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    4d4: 03cd8db3  mul          x27, x27, x28
    4d8: 01bb0b33  add          x22, x22, x27
    4dc: 001b9b93  slli         x23, x23, 1
    4e0: 017b0b33  add          x22, x22, x23
    4e4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4e8: 00008067  jalr         x0, 0(x1)
    4ec: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f0: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f4: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4f8: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    4fc: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    500: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    504: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    508: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    50c: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    510: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    514: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    518: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_51c:
    51c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    520: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    524: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    528: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    52c: 015a6463  bltu         x20, x21, 0x00000534  # target 0x00000534
    530: fedff06f  jal          x0, 0x0000051c  # target 0x0000051c
loc_534:
    534: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    538: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    53c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    540: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    544: 015a6463  bltu         x20, x21, 0x0000054c  # target 0x0000054c
    548: fedff06f  jal          x0, 0x00000534  # target 0x00000534
loc_54c:
    54c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    550: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    554: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    558: 014a1a13  slli         x20, x20, 20
    55c: 014a5a13  srli         x20, x20, 20
    560: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_564:
    564: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    568: 000b0463  beq          x22, x0, 0x00000570  # target 0x00000570
    56c: ff9ff06f  jal          x0, 0x00000564  # target 0x00000564
loc_570:
    570: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    574: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    578: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    57c: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    580: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    584: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    588: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    58c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    590: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    594: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    598: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    59c: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    5a0: 03cba023  sw           x28, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write runtime value
    5a4: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    5a8: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    5ac: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    5b0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    5b4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    5b8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    5bc: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_5c0:
    5c0: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    5c4: 000b0463  beq          x22, x0, 0x000005cc  # target 0x000005cc
    5c8: ff9ff06f  jal          x0, 0x000005c0  # target 0x000005c0
loc_5cc:
    5cc: 00008067  jalr         x0, 0(x1)
loc_5d0:
    5d0: 79000a93  addi         x21, x0, 1936  # x21 = 0x00000790
    5d4: 000aaa03  lw           x20, 0(x21)  # param e2e_k; 0x00000790
    5d8: 007a7d13  andi         x26, x20, 7
    5dc: ff8a7a13  andi         x20, x20, -8
    5e0: 01af8ab3  add          x21, x31, x26
    5e4: 007afb93  andi         x23, x21, 7
    5e8: 003ada93  srli         x21, x21, 3
    5ec: 00ba9a93  slli         x21, x21, 11
    5f0: 014a8ab3  add          x21, x21, x20
    5f4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005f4
    5f8: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000624
    5fc: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    600: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    604: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
    608: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    60c: 03cd8db3  mul          x27, x27, x28
    610: 01bb0b33  add          x22, x22, x27
    614: 001b9b93  slli         x23, x23, 1
    618: 017b0b33  add          x22, x22, x23
    61c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    620: 00008067  jalr         x0, 0(x1)
    624: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    628: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    62c: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    630: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    634: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    638: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    63c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    640: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    644: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    648: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    64c: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    650: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_654:
    654: 79800a93  addi         x21, x0, 1944  # x21 = 0x00000798
    658: 000aaa03  lw           x20, 0(x21)  # param e2e_v; 0x00000798
    65c: 007a7d13  andi         x26, x20, 7
    660: ff8a7a13  andi         x20, x20, -8
    664: 01af8ab3  add          x21, x31, x26
    668: 007afb93  andi         x23, x21, 7
    66c: 003ada93  srli         x21, x21, 3
    670: 00ba9a93  slli         x21, x21, 11
    674: 014a8ab3  add          x21, x21, x20
    678: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000678
    67c: 030b0b13  addi         x22, x22, 48  # x22 = 0x000006a8
    680: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    684: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    688: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
    68c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    690: 03cd8db3  mul          x27, x27, x28
    694: 01bb0b33  add          x22, x22, x27
    698: 001b9b93  slli         x23, x23, 1
    69c: 017b0b33  add          x22, x22, x23
    6a0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6a4: 00008067  jalr         x0, 0(x1)
    6a8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6ac: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6b0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6b4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    6b8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6bc: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6c0: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    6c4: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    6c8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    6cc: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6d0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    6d4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    6d8:           j FW_NCRISC+4   # return to firmware, linked at install
