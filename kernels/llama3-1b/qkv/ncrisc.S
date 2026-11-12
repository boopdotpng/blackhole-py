# llama3 1b decode: qkv, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_l0_q, 0x788=e2e_l0_k, 0x78c=e2e_l0_v, 0x790=e2e_l0_input_norm, 0xe8c0=e2e_q_compact, 0xe8c4=e2e_l0_q_row_start, 0xe8c8=e2e_k_compact, 0xe8cc=e2e_l0_k_row_start, 0xe8d0=e2e_v_compact, 0xe8d4=e2e_l0_v_row_start, 0xe8d8=e2e_l0_q_rows, 0xe8dc=e2e_l0_k_rows, 0xe8e0=e2e_l0_v_rows, 0xe8e4=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
      4: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
      8: 00011437  lui          x8, 0x00011  # x8 = 0x00011000
      c: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00011000
     10: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     14: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     18: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: 00013237  lui          x4, 0x00013  # x4 = 0x00013000
     20: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_24:
     24: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     28: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     2c: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     30: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     34: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     38: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     3c: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     40: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     44: 02020213  addi         x4, x4, 32
     48: ff828293  addi         x5, x5, -8
     4c: fc029ce3  bne          x5, x0, 0x00000024  # target 0x00000024
     50: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
     54: 8d828293  addi         x5, x5, -1832  # x5 = 0x0000e8d8
     58: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0000e8d8
     5c: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     60: 00020313  addi         x6, x4, 0
loc_64:
     64: 0e62f863  bgeu         x5, x6, 0x00000154  # target 0x00000154
     68: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     6c: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
     70: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
     74: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_78:
     78: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
     7c: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
     80: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
     84: 407404b3  sub          x9, x8, x7
     88: 01049493  slli         x9, x9, 16
     8c: 0104d493  srli         x9, x9, 16
     90: 00a4f663  bgeu         x9, x10, 0x0000009c  # target 0x0000009c
     94: 0ff0000f  fence        0xf, 0xf
     98: fe1ff06f  jal          x0, 0x00000078  # target 0x00000078
loc_9c:
     9c: 0ff0000f  fence        0xf, 0xf
     a0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     a4: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
     a8: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
     ac: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
     b0: 00f2f493  andi         x9, x5, 15
     b4: 00149493  slli         x9, x9, 1
     b8: 0102f593  andi         x11, x5, 16
     bc: 00559593  slli         x11, x11, 5
     c0: 00b4e4b3  or           x9, x9, x11
     c4: 1e02f593  andi         x11, x5, 480
     c8: 00b4e4b3  or           x9, x9, x11
     cc: 0092d593  srli         x11, x5, 9
     d0: 00a59593  slli         x11, x11, 10
     d4: 00b4e4b3  or           x9, x9, x11
     d8: 00013537  lui          x10, 0x00013  # x10 = 0x00013000
     dc: 00950533  add          x10, x10, x9
     e0: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
     e4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     e8: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     ec: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     f0: 00138393  addi         x7, x7, 1
     f4: 01039393  slli         x7, x7, 16
     f8: 0103d393  srli         x7, x7, 16
     fc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    100: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    104: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    108: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    10c: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    110: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    114: 0ff0000f  fence        0xf, 0xf
    118: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    11c: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    120: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    124: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    128: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    12c: 008383b3  add          x7, x7, x8
    130: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    134: 0093e663  bltu         x7, x9, 0x00000140  # target 0x00000140
    138: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    13c: 40a383b3  sub          x7, x7, x10
loc_140:
    140: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    144: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    148: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    14c: 00128293  addi         x5, x5, 1
    150: f15ff06f  jal          x0, 0x00000064  # target 0x00000064
loc_154:
    154: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    158: 30c000ef  jal          x1, 0x00000464  # target 0x00000464; x1 = 0x0000015c
    15c: 000a8213  addi         x4, x21, 0
    160: 000b0293  addi         x5, x22, 0
    164: 388000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000168
    168: 3a0000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x0000016c
    16c: 00013fb7  lui          x31, 0x00013  # x31 = 0x00013000
    170: 00020f13  addi         x30, x4, 0
    174: 00028e93  addi         x29, x5, 0
    178: 3ac000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x0000017c
    17c: 370000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000180
    180: 388000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000184
    184: 00014237  lui          x4, 0x00014  # x4 = 0x00014000
    188: 80020213  addi         x4, x4, -2048  # x4 = 0x00013800
    18c: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_190:
    190: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
    194: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
    198: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
    19c: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
    1a0: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
    1a4: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
    1a8: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
    1ac: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
    1b0: 02020213  addi         x4, x4, 32
    1b4: ff828293  addi         x5, x5, -8
    1b8: fc029ce3  bne          x5, x0, 0x00000190  # target 0x00000190
    1bc: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    1c0: 8dc28293  addi         x5, x5, -1828  # x5 = 0x0000e8dc
    1c4: 0002a203  lw           x4, 0(x5)  # param e2e_l0_k_rows; 0x0000e8dc
    1c8: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    1cc: 00020313  addi         x6, x4, 0
loc_1d0:
    1d0: 0e62fa63  bgeu         x5, x6, 0x000002c4  # target 0x000002c4
    1d4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1d8: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
    1dc: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
    1e0: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_1e4:
    1e4: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
    1e8: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
    1ec: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
    1f0: 407404b3  sub          x9, x8, x7
    1f4: 01049493  slli         x9, x9, 16
    1f8: 0104d493  srli         x9, x9, 16
    1fc: 00a4f663  bgeu         x9, x10, 0x00000208  # target 0x00000208
    200: 0ff0000f  fence        0xf, 0xf
    204: fe1ff06f  jal          x0, 0x000001e4  # target 0x000001e4
loc_208:
    208: 0ff0000f  fence        0xf, 0xf
    20c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    210: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    214: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    218: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
    21c: 00f2f493  andi         x9, x5, 15
    220: 00149493  slli         x9, x9, 1
    224: 0102f593  andi         x11, x5, 16
    228: 00559593  slli         x11, x11, 5
    22c: 00b4e4b3  or           x9, x9, x11
    230: 1e02f593  andi         x11, x5, 480
    234: 00b4e4b3  or           x9, x9, x11
    238: 0092d593  srli         x11, x5, 9
    23c: 00a59593  slli         x11, x11, 10
    240: 00b4e4b3  or           x9, x9, x11
    244: 00014537  lui          x10, 0x00014  # x10 = 0x00014000
    248: 80050513  addi         x10, x10, -2048  # x10 = 0x00013800
    24c: 00950533  add          x10, x10, x9
    250: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
    254: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    258: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    25c: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    260: 00138393  addi         x7, x7, 1
    264: 01039393  slli         x7, x7, 16
    268: 0103d393  srli         x7, x7, 16
    26c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    270: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    274: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    278: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    27c: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    280: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    284: 0ff0000f  fence        0xf, 0xf
    288: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    28c: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    290: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    294: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    298: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    29c: 008383b3  add          x7, x7, x8
    2a0: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2a4: 0093e663  bltu         x7, x9, 0x000002b0  # target 0x000002b0
    2a8: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2ac: 40a383b3  sub          x7, x7, x10
loc_2b0:
    2b0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    2b4: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    2b8: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    2bc: 00128293  addi         x5, x5, 1
    2c0: f11ff06f  jal          x0, 0x000001d0  # target 0x000001d0
loc_2c4:
    2c4: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    2c8: 318000ef  jal          x1, 0x000005e0  # target 0x000005e0; x1 = 0x000002cc
    2cc: 000a8213  addi         x4, x21, 0
    2d0: 000b0293  addi         x5, x22, 0
    2d4: 218000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x000002d8
    2d8: 230000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x000002dc
    2dc: 00014fb7  lui          x31, 0x00014  # x31 = 0x00014000
    2e0: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00013800
    2e4: 00020f13  addi         x30, x4, 0
    2e8: 00028e93  addi         x29, x5, 0
    2ec: 238000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x000002f0
    2f0: 1fc000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x000002f4
    2f4: 214000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x000002f8
    2f8: 00014237  lui          x4, 0x00014  # x4 = 0x00014000
    2fc: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_300:
    300: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
    304: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
    308: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
    30c: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
    310: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
    314: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
    318: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
    31c: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
    320: 02020213  addi         x4, x4, 32
    324: ff828293  addi         x5, x5, -8
    328: fc029ce3  bne          x5, x0, 0x00000300  # target 0x00000300
    32c: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    330: 8e028293  addi         x5, x5, -1824  # x5 = 0x0000e8e0
    334: 0002a203  lw           x4, 0(x5)  # param e2e_l0_v_rows; 0x0000e8e0
    338: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    33c: 00020313  addi         x6, x4, 0
loc_340:
    340: 0e62f863  bgeu         x5, x6, 0x00000430  # target 0x00000430
    344: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    348: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
    34c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
    350: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_354:
    354: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
    358: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
    35c: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
    360: 407404b3  sub          x9, x8, x7
    364: 01049493  slli         x9, x9, 16
    368: 0104d493  srli         x9, x9, 16
    36c: 00a4f663  bgeu         x9, x10, 0x00000378  # target 0x00000378
    370: 0ff0000f  fence        0xf, 0xf
    374: fe1ff06f  jal          x0, 0x00000354  # target 0x00000354
loc_378:
    378: 0ff0000f  fence        0xf, 0xf
    37c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    380: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    384: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    388: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
    38c: 00f2f493  andi         x9, x5, 15
    390: 00149493  slli         x9, x9, 1
    394: 0102f593  andi         x11, x5, 16
    398: 00559593  slli         x11, x11, 5
    39c: 00b4e4b3  or           x9, x9, x11
    3a0: 1e02f593  andi         x11, x5, 480
    3a4: 00b4e4b3  or           x9, x9, x11
    3a8: 0092d593  srli         x11, x5, 9
    3ac: 00a59593  slli         x11, x11, 10
    3b0: 00b4e4b3  or           x9, x9, x11
    3b4: 00014537  lui          x10, 0x00014  # x10 = 0x00014000
    3b8: 00950533  add          x10, x10, x9
    3bc: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
    3c0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    3c4: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    3c8: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    3cc: 00138393  addi         x7, x7, 1
    3d0: 01039393  slli         x7, x7, 16
    3d4: 0103d393  srli         x7, x7, 16
    3d8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    3dc: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    3e0: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    3e4: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    3e8: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    3ec: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    3f0: 0ff0000f  fence        0xf, 0xf
    3f4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    3f8: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    3fc: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    400: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    404: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    408: 008383b3  add          x7, x7, x8
    40c: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    410: 0093e663  bltu         x7, x9, 0x0000041c  # target 0x0000041c
    414: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    418: 40a383b3  sub          x7, x7, x10
loc_41c:
    41c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    420: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    424: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    428: 00128293  addi         x5, x5, 1
    42c: f15ff06f  jal          x0, 0x00000340  # target 0x00000340
loc_430:
    430: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    434: 234000ef  jal          x1, 0x00000668  # target 0x00000668; x1 = 0x00000438
    438: 000a8213  addi         x4, x21, 0
    43c: 000b0293  addi         x5, x22, 0
    440: 0ac000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000444
    444: 0c4000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000448
    448: 00014fb7  lui          x31, 0x00014  # x31 = 0x00014000
    44c: 00020f13  addi         x30, x4, 0
    450: 00028e93  addi         x29, x5, 0
    454: 0d0000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x00000458
    458: 094000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x0000045c
    45c: 0ac000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000460
    460: 2900006f  jal          x0, 0x000006f0  # target 0x000006f0
loc_464:
    464: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    468: 8c0a8a93  addi         x21, x21, -1856  # x21 = 0x0000e8c0
    46c: 000aaa03  lw           x20, 0(x21)  # param e2e_q_compact; 0x0000e8c0
    470: 007a7d13  andi         x26, x20, 7
    474: ff8a7a13  andi         x20, x20, -8
    478: 01af8ab3  add          x21, x31, x26
    47c: 007afb93  andi         x23, x21, 7
    480: 003ada93  srli         x21, x21, 3
    484: 00ba9a93  slli         x21, x21, 11
    488: 014a8ab3  add          x21, x21, x20
    48c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000048c
    490: 030b0b13  addi         x22, x22, 48  # x22 = 0x000004bc
    494: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    498: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    49c: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    4a0: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    4a4: 03cd8db3  mul          x27, x27, x28
    4a8: 01bb0b33  add          x22, x22, x27
    4ac: 001b9b93  slli         x23, x23, 1
    4b0: 017b0b33  add          x22, x22, x23
    4b4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4b8: 00008067  jalr         x0, 0(x1)
    4bc: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4c0: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4c4: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4c8: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    4cc: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4d0: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4d4: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    4d8: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    4dc: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    4e0: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4e4: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    4e8: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_4ec:
    4ec: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    4f0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    4f4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    4f8: 000a0463  beq          x20, x0, 0x00000500  # target 0x00000500
    4fc: ff1ff06f  jal          x0, 0x000004ec  # target 0x000004ec
loc_500:
    500: 0ff0000f  fence        0xf, 0xf
    504: 00008067  jalr         x0, 0(x1)
loc_508:
    508: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    50c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    510: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    514: 000a0463  beq          x20, x0, 0x0000051c  # target 0x0000051c
    518: ff1ff06f  jal          x0, 0x00000508  # target 0x00000508
loc_51c:
    51c: 0ff0000f  fence        0xf, 0xf
    520: 00008067  jalr         x0, 0(x1)
loc_524:
    524: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    528: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    52c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    530: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    534: 015a6463  bltu         x20, x21, 0x0000053c  # target 0x0000053c
    538: fedff06f  jal          x0, 0x00000524  # target 0x00000524
loc_53c:
    53c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    540: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    544: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    548: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    54c: 015a6463  bltu         x20, x21, 0x00000554  # target 0x00000554
    550: fedff06f  jal          x0, 0x0000053c  # target 0x0000053c
loc_554:
    554: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    558: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    55c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    560: 014a1a13  slli         x20, x20, 20
    564: 014a5a13  srli         x20, x20, 20
    568: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_56c:
    56c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    570: 000b0463  beq          x22, x0, 0x00000578  # target 0x00000578
    574: ff9ff06f  jal          x0, 0x0000056c  # target 0x0000056c
loc_578:
    578: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    57c: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    580: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    584: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    588: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    58c: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    590: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    594: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    598: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    59c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    5a0: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    5a4: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    5a8: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5ac: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    5b0: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    5b4: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    5b8: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    5bc: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    5c0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    5c4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    5c8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    5cc: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_5d0:
    5d0: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    5d4: 000b0463  beq          x22, x0, 0x000005dc  # target 0x000005dc
    5d8: ff9ff06f  jal          x0, 0x000005d0  # target 0x000005d0
loc_5dc:
    5dc: 00008067  jalr         x0, 0(x1)
loc_5e0:
    5e0: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    5e4: 8c8a8a93  addi         x21, x21, -1848  # x21 = 0x0000e8c8
    5e8: 000aaa03  lw           x20, 0(x21)  # param e2e_k_compact; 0x0000e8c8
    5ec: 007a7d13  andi         x26, x20, 7
    5f0: ff8a7a13  andi         x20, x20, -8
    5f4: 01af8ab3  add          x21, x31, x26
    5f8: 007afb93  andi         x23, x21, 7
    5fc: 003ada93  srli         x21, x21, 3
    600: 00ba9a93  slli         x21, x21, 11
    604: 014a8ab3  add          x21, x21, x20
    608: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000608
    60c: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000638
    610: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    614: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    618: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    61c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    620: 03cd8db3  mul          x27, x27, x28
    624: 01bb0b33  add          x22, x22, x27
    628: 001b9b93  slli         x23, x23, 1
    62c: 017b0b33  add          x22, x22, x23
    630: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    634: 00008067  jalr         x0, 0(x1)
    638: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    63c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    640: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    644: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    648: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    64c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    650: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    654: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    658: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    65c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    660: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    664: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_668:
    668: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    66c: 8d0a8a93  addi         x21, x21, -1840  # x21 = 0x0000e8d0
    670: 000aaa03  lw           x20, 0(x21)  # param e2e_v_compact; 0x0000e8d0
    674: 007a7d13  andi         x26, x20, 7
    678: ff8a7a13  andi         x20, x20, -8
    67c: 01af8ab3  add          x21, x31, x26
    680: 007afb93  andi         x23, x21, 7
    684: 003ada93  srli         x21, x21, 3
    688: 00ba9a93  slli         x21, x21, 11
    68c: 014a8ab3  add          x21, x21, x20
    690: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000690
    694: 030b0b13  addi         x22, x22, 48  # x22 = 0x000006c0
    698: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    69c: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    6a0: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    6a4: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    6a8: 03cd8db3  mul          x27, x27, x28
    6ac: 01bb0b33  add          x22, x22, x27
    6b0: 001b9b93  slli         x23, x23, 1
    6b4: 017b0b33  add          x22, x22, x23
    6b8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6bc: 00008067  jalr         x0, 0(x1)
    6c0: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6c4: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6c8: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6cc: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    6d0: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6d4: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6d8: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    6dc: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    6e0: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    6e4: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6e8: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    6ec: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    6f0:           j FW_NCRISC+4   # return to firmware, linked at install
