# llama3 1b decode: qkv, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_l0_q, 0x788=e2e_l0_k, 0x78c=e2e_l0_v, 0x790=e2e_l0_input_norm, 0xe8c0=e2e_q_compact, 0xe8c4=e2e_l0_q_row_start, 0xe8c8=e2e_k_compact, 0xe8cc=e2e_l0_k_row_start, 0xe8d0=e2e_v_compact, 0xe8d4=e2e_l0_v_row_start, 0xe8d8=e2e_l0_q_rows, 0xe8dc=e2e_l0_k_rows, 0xe8e0=e2e_l0_v_rows, 0xe8e4=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
      4: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
      8: 00011437  lui          x8, 0x00011  # x8 = 0x00011000
      c: fc040413  addi         x8, x8, -64  # x8 = 0x00010fc0
     10: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00010fc0
     14: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     18: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: 00013237  lui          x4, 0x00013  # x4 = 0x00013000
     24: fc020213  addi         x4, x4, -64  # x4 = 0x00012fc0
     28: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_2c:
     2c: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     30: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     34: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     38: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     3c: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     40: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     44: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     48: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     4c: 02020213  addi         x4, x4, 32
     50: ff828293  addi         x5, x5, -8
     54: fc029ce3  bne          x5, x0, 0x0000002c  # target 0x0000002c
     58: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
     5c: 8d828293  addi         x5, x5, -1832  # x5 = 0x0000e8d8
     60: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0000e8d8
     64: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     68: 00020313  addi         x6, x4, 0
loc_6c:
     6c: 0e62fc63  bgeu         x5, x6, 0x00000164  # target 0x00000164
     70: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     74: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
     78: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
     7c: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_80:
     80: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
     84: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
     88: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
     8c: 407404b3  sub          x9, x8, x7
     90: 01049493  slli         x9, x9, 16
     94: 0104d493  srli         x9, x9, 16
     98: 00a4f663  bgeu         x9, x10, 0x000000a4  # target 0x000000a4
     9c: 0ff0000f  fence        0xf, 0xf
     a0: fe1ff06f  jal          x0, 0x00000080  # target 0x00000080
loc_a4:
     a4: 0ff0000f  fence        0xf, 0xf
     a8: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     ac: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
     b0: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
     b4: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
     b8: 00f2f493  andi         x9, x5, 15
     bc: 00149493  slli         x9, x9, 1
     c0: 0102f593  andi         x11, x5, 16
     c4: 00559593  slli         x11, x11, 5
     c8: 00b4e4b3  or           x9, x9, x11
     cc: 1e02f593  andi         x11, x5, 480
     d0: 00b4e4b3  or           x9, x9, x11
     d4: 0092d593  srli         x11, x5, 9
     d8: 00a59593  slli         x11, x11, 10
     dc: 00b4e4b3  or           x9, x9, x11
     e0: 00013537  lui          x10, 0x00013  # x10 = 0x00013000
     e4: fc050513  addi         x10, x10, -64  # x10 = 0x00012fc0
     e8: 00950533  add          x10, x10, x9
     ec: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
     f0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     f4: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     f8: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     fc: 00138393  addi         x7, x7, 1
    100: 01039393  slli         x7, x7, 16
    104: 0103d393  srli         x7, x7, 16
    108: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    10c: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    110: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    114: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    118: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    11c: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    120: 0ff0000f  fence        0xf, 0xf
    124: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    128: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    12c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    130: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    134: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    138: 008383b3  add          x7, x7, x8
    13c: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    140: fc048493  addi         x9, x9, -64  # x9 = 0x00011fc0
    144: 0093e663  bltu         x7, x9, 0x00000150  # target 0x00000150
    148: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    14c: 40a383b3  sub          x7, x7, x10
loc_150:
    150: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    154: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    158: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    15c: 00128293  addi         x5, x5, 1
    160: f0dff06f  jal          x0, 0x0000006c  # target 0x0000006c
loc_164:
    164: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    168: 324000ef  jal          x1, 0x0000048c  # target 0x0000048c; x1 = 0x0000016c
    16c: 000a8213  addi         x4, x21, 0
    170: 000b0293  addi         x5, x22, 0
    174: 3a0000ef  jal          x1, 0x00000514  # target 0x00000514; x1 = 0x00000178
    178: 3b8000ef  jal          x1, 0x00000530  # target 0x00000530; x1 = 0x0000017c
    17c: 00013fb7  lui          x31, 0x00013  # x31 = 0x00013000
    180: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00012fc0
    184: 00020f13  addi         x30, x4, 0
    188: 00028e93  addi         x29, x5, 0
    18c: 3c0000ef  jal          x1, 0x0000054c  # target 0x0000054c; x1 = 0x00000190
    190: 384000ef  jal          x1, 0x00000514  # target 0x00000514; x1 = 0x00000194
    194: 39c000ef  jal          x1, 0x00000530  # target 0x00000530; x1 = 0x00000198
    198: 00013237  lui          x4, 0x00013  # x4 = 0x00013000
    19c: 7c020213  addi         x4, x4, 1984  # x4 = 0x000137c0
    1a0: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_1a4:
    1a4: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
    1a8: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
    1ac: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
    1b0: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
    1b4: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
    1b8: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
    1bc: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
    1c0: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
    1c4: 02020213  addi         x4, x4, 32
    1c8: ff828293  addi         x5, x5, -8
    1cc: fc029ce3  bne          x5, x0, 0x000001a4  # target 0x000001a4
    1d0: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    1d4: 8dc28293  addi         x5, x5, -1828  # x5 = 0x0000e8dc
    1d8: 0002a203  lw           x4, 0(x5)  # param e2e_l0_k_rows; 0x0000e8dc
    1dc: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    1e0: 00020313  addi         x6, x4, 0
loc_1e4:
    1e4: 0e62fc63  bgeu         x5, x6, 0x000002dc  # target 0x000002dc
    1e8: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1ec: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
    1f0: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
    1f4: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_1f8:
    1f8: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
    1fc: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
    200: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
    204: 407404b3  sub          x9, x8, x7
    208: 01049493  slli         x9, x9, 16
    20c: 0104d493  srli         x9, x9, 16
    210: 00a4f663  bgeu         x9, x10, 0x0000021c  # target 0x0000021c
    214: 0ff0000f  fence        0xf, 0xf
    218: fe1ff06f  jal          x0, 0x000001f8  # target 0x000001f8
loc_21c:
    21c: 0ff0000f  fence        0xf, 0xf
    220: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    224: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    228: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    22c: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
    230: 00f2f493  andi         x9, x5, 15
    234: 00149493  slli         x9, x9, 1
    238: 0102f593  andi         x11, x5, 16
    23c: 00559593  slli         x11, x11, 5
    240: 00b4e4b3  or           x9, x9, x11
    244: 1e02f593  andi         x11, x5, 480
    248: 00b4e4b3  or           x9, x9, x11
    24c: 0092d593  srli         x11, x5, 9
    250: 00a59593  slli         x11, x11, 10
    254: 00b4e4b3  or           x9, x9, x11
    258: 00013537  lui          x10, 0x00013  # x10 = 0x00013000
    25c: 7c050513  addi         x10, x10, 1984  # x10 = 0x000137c0
    260: 00950533  add          x10, x10, x9
    264: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
    268: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    26c: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    270: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    274: 00138393  addi         x7, x7, 1
    278: 01039393  slli         x7, x7, 16
    27c: 0103d393  srli         x7, x7, 16
    280: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    284: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    288: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    28c: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    290: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    294: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    298: 0ff0000f  fence        0xf, 0xf
    29c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    2a0: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    2a4: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    2a8: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2ac: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    2b0: 008383b3  add          x7, x7, x8
    2b4: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2b8: fc048493  addi         x9, x9, -64  # x9 = 0x00011fc0
    2bc: 0093e663  bltu         x7, x9, 0x000002c8  # target 0x000002c8
    2c0: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2c4: 40a383b3  sub          x7, x7, x10
loc_2c8:
    2c8: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    2cc: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    2d0: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    2d4: 00128293  addi         x5, x5, 1
    2d8: f0dff06f  jal          x0, 0x000001e4  # target 0x000001e4
loc_2dc:
    2dc: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    2e0: 328000ef  jal          x1, 0x00000608  # target 0x00000608; x1 = 0x000002e4
    2e4: 000a8213  addi         x4, x21, 0
    2e8: 000b0293  addi         x5, x22, 0
    2ec: 228000ef  jal          x1, 0x00000514  # target 0x00000514; x1 = 0x000002f0
    2f0: 240000ef  jal          x1, 0x00000530  # target 0x00000530; x1 = 0x000002f4
    2f4: 00013fb7  lui          x31, 0x00013  # x31 = 0x00013000
    2f8: 7c0f8f93  addi         x31, x31, 1984  # x31 = 0x000137c0
    2fc: 00020f13  addi         x30, x4, 0
    300: 00028e93  addi         x29, x5, 0
    304: 248000ef  jal          x1, 0x0000054c  # target 0x0000054c; x1 = 0x00000308
    308: 20c000ef  jal          x1, 0x00000514  # target 0x00000514; x1 = 0x0000030c
    30c: 224000ef  jal          x1, 0x00000530  # target 0x00000530; x1 = 0x00000310
    310: 00014237  lui          x4, 0x00014  # x4 = 0x00014000
    314: fc020213  addi         x4, x4, -64  # x4 = 0x00013fc0
    318: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_31c:
    31c: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
    320: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
    324: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
    328: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
    32c: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
    330: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
    334: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
    338: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
    33c: 02020213  addi         x4, x4, 32
    340: ff828293  addi         x5, x5, -8
    344: fc029ce3  bne          x5, x0, 0x0000031c  # target 0x0000031c
    348: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    34c: 8e028293  addi         x5, x5, -1824  # x5 = 0x0000e8e0
    350: 0002a203  lw           x4, 0(x5)  # param e2e_l0_v_rows; 0x0000e8e0
    354: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    358: 00020313  addi         x6, x4, 0
loc_35c:
    35c: 0e62fc63  bgeu         x5, x6, 0x00000454  # target 0x00000454
    360: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    364: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
    368: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
    36c: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_370:
    370: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
    374: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
    378: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
    37c: 407404b3  sub          x9, x8, x7
    380: 01049493  slli         x9, x9, 16
    384: 0104d493  srli         x9, x9, 16
    388: 00a4f663  bgeu         x9, x10, 0x00000394  # target 0x00000394
    38c: 0ff0000f  fence        0xf, 0xf
    390: fe1ff06f  jal          x0, 0x00000370  # target 0x00000370
loc_394:
    394: 0ff0000f  fence        0xf, 0xf
    398: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    39c: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    3a0: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    3a4: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
    3a8: 00f2f493  andi         x9, x5, 15
    3ac: 00149493  slli         x9, x9, 1
    3b0: 0102f593  andi         x11, x5, 16
    3b4: 00559593  slli         x11, x11, 5
    3b8: 00b4e4b3  or           x9, x9, x11
    3bc: 1e02f593  andi         x11, x5, 480
    3c0: 00b4e4b3  or           x9, x9, x11
    3c4: 0092d593  srli         x11, x5, 9
    3c8: 00a59593  slli         x11, x11, 10
    3cc: 00b4e4b3  or           x9, x9, x11
    3d0: 00014537  lui          x10, 0x00014  # x10 = 0x00014000
    3d4: fc050513  addi         x10, x10, -64  # x10 = 0x00013fc0
    3d8: 00950533  add          x10, x10, x9
    3dc: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
    3e0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    3e4: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    3e8: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    3ec: 00138393  addi         x7, x7, 1
    3f0: 01039393  slli         x7, x7, 16
    3f4: 0103d393  srli         x7, x7, 16
    3f8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    3fc: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    400: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    404: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    408: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    40c: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    410: 0ff0000f  fence        0xf, 0xf
    414: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    418: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    41c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    420: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    424: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    428: 008383b3  add          x7, x7, x8
    42c: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    430: fc048493  addi         x9, x9, -64  # x9 = 0x00011fc0
    434: 0093e663  bltu         x7, x9, 0x00000440  # target 0x00000440
    438: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    43c: 40a383b3  sub          x7, x7, x10
loc_440:
    440: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    444: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    448: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    44c: 00128293  addi         x5, x5, 1
    450: f0dff06f  jal          x0, 0x0000035c  # target 0x0000035c
loc_454:
    454: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    458: 238000ef  jal          x1, 0x00000690  # target 0x00000690; x1 = 0x0000045c
    45c: 000a8213  addi         x4, x21, 0
    460: 000b0293  addi         x5, x22, 0
    464: 0b0000ef  jal          x1, 0x00000514  # target 0x00000514; x1 = 0x00000468
    468: 0c8000ef  jal          x1, 0x00000530  # target 0x00000530; x1 = 0x0000046c
    46c: 00014fb7  lui          x31, 0x00014  # x31 = 0x00014000
    470: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00013fc0
    474: 00020f13  addi         x30, x4, 0
    478: 00028e93  addi         x29, x5, 0
    47c: 0d0000ef  jal          x1, 0x0000054c  # target 0x0000054c; x1 = 0x00000480
    480: 094000ef  jal          x1, 0x00000514  # target 0x00000514; x1 = 0x00000484
    484: 0ac000ef  jal          x1, 0x00000530  # target 0x00000530; x1 = 0x00000488
    488: 2900006f  jal          x0, 0x00000718  # target 0x00000718
loc_48c:
    48c: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    490: 8c0a8a93  addi         x21, x21, -1856  # x21 = 0x0000e8c0
    494: 000aaa03  lw           x20, 0(x21)  # param e2e_q_compact; 0x0000e8c0
    498: 007a7d13  andi         x26, x20, 7
    49c: ff8a7a13  andi         x20, x20, -8
    4a0: 01af8ab3  add          x21, x31, x26
    4a4: 007afb93  andi         x23, x21, 7
    4a8: 003ada93  srli         x21, x21, 3
    4ac: 00ba9a93  slli         x21, x21, 11
    4b0: 014a8ab3  add          x21, x21, x20
    4b4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004b4
    4b8: 030b0b13  addi         x22, x22, 48  # x22 = 0x000004e4
    4bc: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    4c0: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    4c4: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    4c8: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    4cc: 03cd8db3  mul          x27, x27, x28
    4d0: 01bb0b33  add          x22, x22, x27
    4d4: 001b9b93  slli         x23, x23, 1
    4d8: 017b0b33  add          x22, x22, x23
    4dc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4e0: 00008067  jalr         x0, 0(x1)
    4e4: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4e8: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4ec: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4f0: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    4f4: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f8: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4fc: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    500: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    504: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    508: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    50c: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    510: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_514:
    514: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    518: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    51c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    520: 000a0463  beq          x20, x0, 0x00000528  # target 0x00000528
    524: ff1ff06f  jal          x0, 0x00000514  # target 0x00000514
loc_528:
    528: 0ff0000f  fence        0xf, 0xf
    52c: 00008067  jalr         x0, 0(x1)
loc_530:
    530: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    534: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    538: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    53c: 000a0463  beq          x20, x0, 0x00000544  # target 0x00000544
    540: ff1ff06f  jal          x0, 0x00000530  # target 0x00000530
loc_544:
    544: 0ff0000f  fence        0xf, 0xf
    548: 00008067  jalr         x0, 0(x1)
loc_54c:
    54c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    550: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    554: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    558: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    55c: 015a6463  bltu         x20, x21, 0x00000564  # target 0x00000564
    560: fedff06f  jal          x0, 0x0000054c  # target 0x0000054c
loc_564:
    564: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    568: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    56c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    570: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    574: 015a6463  bltu         x20, x21, 0x0000057c  # target 0x0000057c
    578: fedff06f  jal          x0, 0x00000564  # target 0x00000564
loc_57c:
    57c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    580: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    584: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    588: 014a1a13  slli         x20, x20, 20
    58c: 014a5a13  srli         x20, x20, 20
    590: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_594:
    594: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    598: 000b0463  beq          x22, x0, 0x000005a0  # target 0x000005a0
    59c: ff9ff06f  jal          x0, 0x00000594  # target 0x00000594
loc_5a0:
    5a0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    5a4: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    5a8: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    5ac: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    5b0: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    5b4: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    5b8: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    5bc: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    5c0: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    5c4: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    5c8: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    5cc: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    5d0: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5d4: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    5d8: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    5dc: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    5e0: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    5e4: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    5e8: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    5ec: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    5f0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    5f4: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_5f8:
    5f8: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    5fc: 000b0463  beq          x22, x0, 0x00000604  # target 0x00000604
    600: ff9ff06f  jal          x0, 0x000005f8  # target 0x000005f8
loc_604:
    604: 00008067  jalr         x0, 0(x1)
loc_608:
    608: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    60c: 8c8a8a93  addi         x21, x21, -1848  # x21 = 0x0000e8c8
    610: 000aaa03  lw           x20, 0(x21)  # param e2e_k_compact; 0x0000e8c8
    614: 007a7d13  andi         x26, x20, 7
    618: ff8a7a13  andi         x20, x20, -8
    61c: 01af8ab3  add          x21, x31, x26
    620: 007afb93  andi         x23, x21, 7
    624: 003ada93  srli         x21, x21, 3
    628: 00ba9a93  slli         x21, x21, 11
    62c: 014a8ab3  add          x21, x21, x20
    630: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000630
    634: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000660
    638: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    63c: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    640: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    644: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    648: 03cd8db3  mul          x27, x27, x28
    64c: 01bb0b33  add          x22, x22, x27
    650: 001b9b93  slli         x23, x23, 1
    654: 017b0b33  add          x22, x22, x23
    658: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    65c: 00008067  jalr         x0, 0(x1)
    660: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    664: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    668: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    66c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    670: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    674: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    678: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    67c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    680: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    684: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    688: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    68c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_690:
    690: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    694: 8d0a8a93  addi         x21, x21, -1840  # x21 = 0x0000e8d0
    698: 000aaa03  lw           x20, 0(x21)  # param e2e_v_compact; 0x0000e8d0
    69c: 007a7d13  andi         x26, x20, 7
    6a0: ff8a7a13  andi         x20, x20, -8
    6a4: 01af8ab3  add          x21, x31, x26
    6a8: 007afb93  andi         x23, x21, 7
    6ac: 003ada93  srli         x21, x21, 3
    6b0: 00ba9a93  slli         x21, x21, 11
    6b4: 014a8ab3  add          x21, x21, x20
    6b8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000006b8
    6bc: 030b0b13  addi         x22, x22, 48  # x22 = 0x000006e8
    6c0: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    6c4: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    6c8: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    6cc: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    6d0: 03cd8db3  mul          x27, x27, x28
    6d4: 01bb0b33  add          x22, x22, x27
    6d8: 001b9b93  slli         x23, x23, 1
    6dc: 017b0b33  add          x22, x22, x23
    6e0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6e4: 00008067  jalr         x0, 0(x1)
    6e8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6ec: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6f0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6f4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    6f8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6fc: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    700: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    704: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    708: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    70c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    710: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    714: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    718:           j FW_NCRISC+4   # return to firmware, linked at install
