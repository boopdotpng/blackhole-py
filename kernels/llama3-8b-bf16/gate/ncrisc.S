# llama3 8b-bf16 decode: gate, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_b_decode_token, 0x784=e2e_l0_gate, 0x788=e2e_l0_up, 0x78c=e2e_hidden_dense, 0x790=e2e_l0_post_norm, 0xe940=e2e_gate, 0xe944=e2e_l0_gate_row_start, 0xe948=e2e_up, 0xe94c=e2e_l0_up_row_start, 0xe950=dense_start, 0xe954=e2e_l0_gate_rows, 0xe958=e2e_l0_up_rows, 0xe95c=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
      4: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
      8: 00013437  lui          x8, 0x00013  # x8 = 0x00013000
      c: fc040413  addi         x8, x8, -64  # x8 = 0x00012fc0
     10: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00012fc0
     14: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     18: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     28: 000162b7  lui          x5, 0x00016  # x5 = 0x00016000
     2c: fc028293  addi         x5, x5, -64  # x5 = 0x00015fc0
     30: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x00015fc0
     34: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     38: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     3c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     40: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     44: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     48: 000162b7  lui          x5, 0x00016  # x5 = 0x00016000
     4c: 7c028293  addi         x5, x5, 1984  # x5 = 0x000167c0
     50: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x000167c0
     54: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     58: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     5c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     60: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     64: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     68: 0001b2b7  lui          x5, 0x0001b  # x5 = 0x0001b000
     6c: fc028293  addi         x5, x5, -64  # x5 = 0x0001afc0
     70: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x0001afc0
     74: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     78: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     7c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00000000
     80: 00016237  lui          x4, 0x00016  # x4 = 0x00016000
     84: fc020213  addi         x4, x4, -64  # x4 = 0x00015fc0
     88: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_8c:
     8c: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     90: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     94: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     98: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     9c: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     a0: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     a4: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     a8: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     ac: 02020213  addi         x4, x4, 32
     b0: ff828293  addi         x5, x5, -8
     b4: fc029ce3  bne          x5, x0, 0x0000008c  # target 0x0000008c
     b8: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
     bc: 95428293  addi         x5, x5, -1708  # x5 = 0x0000e954
     c0: 0002a203  lw           x4, 0(x5)  # param e2e_l0_gate_rows; 0x0000e954
     c4: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     c8: 00020313  addi         x6, x4, 0
loc_cc:
     cc: 0e62fc63  bgeu         x5, x6, 0x000001c4  # target 0x000001c4
     d0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     d4: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
     d8: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
     dc: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_e0:
     e0: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
     e4: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
     e8: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
     ec: 407404b3  sub          x9, x8, x7
     f0: 01049493  slli         x9, x9, 16
     f4: 0104d493  srli         x9, x9, 16
     f8: 00a4f663  bgeu         x9, x10, 0x00000104  # target 0x00000104
     fc: 0ff0000f  fence        0xf, 0xf
    100: fe1ff06f  jal          x0, 0x000000e0  # target 0x000000e0
loc_104:
    104: 0ff0000f  fence        0xf, 0xf
    108: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    10c: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    110: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    114: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
    118: 00f2f493  andi         x9, x5, 15
    11c: 00149493  slli         x9, x9, 1
    120: 0102f593  andi         x11, x5, 16
    124: 00559593  slli         x11, x11, 5
    128: 00b4e4b3  or           x9, x9, x11
    12c: 1e02f593  andi         x11, x5, 480
    130: 00b4e4b3  or           x9, x9, x11
    134: 0092d593  srli         x11, x5, 9
    138: 00a59593  slli         x11, x11, 10
    13c: 00b4e4b3  or           x9, x9, x11
    140: 00016537  lui          x10, 0x00016  # x10 = 0x00016000
    144: fc050513  addi         x10, x10, -64  # x10 = 0x00015fc0
    148: 00950533  add          x10, x10, x9
    14c: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
    150: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    154: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    158: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    15c: 00138393  addi         x7, x7, 1
    160: 01039393  slli         x7, x7, 16
    164: 0103d393  srli         x7, x7, 16
    168: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    16c: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    170: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    174: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    178: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    17c: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    180: 0ff0000f  fence        0xf, 0xf
    184: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    188: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    18c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    190: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    194: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    198: 008383b3  add          x7, x7, x8
    19c: 000144b7  lui          x9, 0x00014  # x9 = 0x00014000
    1a0: fc048493  addi         x9, x9, -64  # x9 = 0x00013fc0
    1a4: 0093e663  bltu         x7, x9, 0x000001b0  # target 0x000001b0
    1a8: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1ac: 40a383b3  sub          x7, x7, x10
loc_1b0:
    1b0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1b4: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    1b8: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    1bc: 00128293  addi         x5, x5, 1
    1c0: f0dff06f  jal          x0, 0x000000cc  # target 0x000000cc
loc_1c4:
    1c4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1c8: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1cc: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    1d0: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1d4: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    1d8: 00520233  add          x4, x4, x5
    1dc: 00016337  lui          x6, 0x00016  # x6 = 0x00016000
    1e0: 7c030313  addi         x6, x6, 1984  # x6 = 0x000167c0
    1e4: 00626863  bltu         x4, x6, 0x000001f4  # target 0x000001f4
    1e8: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1ec: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    1f0: 40720233  sub          x4, x4, x7
loc_1f4:
    1f4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1f8: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1fc: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    200: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    204: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    208: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    20c: 00120213  addi         x4, x4, 1
    210: 01021213  slli         x4, x4, 16
    214: 01025213  srli         x4, x4, 16
    218: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    21c: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    220: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    224: ffb4b2b7  lui          x5, 0xffb4b  # x5 = 0xffb4b000
    228: 02828293  addi         x5, x5, 40  # x5 = 0xffb4b028
    22c: 0042a023  sw           x4, 0(x5)  # 0xffb4b028; write runtime value
    230: 0ff0000f  fence        0xf, 0xf
    234: 00016237  lui          x4, 0x00016  # x4 = 0x00016000
    238: 7c020213  addi         x4, x4, 1984  # x4 = 0x000167c0
    23c: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_240:
    240: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
    244: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
    248: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
    24c: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
    250: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
    254: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
    258: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
    25c: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
    260: 02020213  addi         x4, x4, 32
    264: ff828293  addi         x5, x5, -8
    268: fc029ce3  bne          x5, x0, 0x00000240  # target 0x00000240
    26c: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    270: 95828293  addi         x5, x5, -1704  # x5 = 0x0000e958
    274: 0002a203  lw           x4, 0(x5)  # param e2e_l0_up_rows; 0x0000e958
    278: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    27c: 00020313  addi         x6, x4, 0
loc_280:
    280: 0e62fc63  bgeu         x5, x6, 0x00000378  # target 0x00000378
    284: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    288: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
    28c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
    290: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_294:
    294: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
    298: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
    29c: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
    2a0: 407404b3  sub          x9, x8, x7
    2a4: 01049493  slli         x9, x9, 16
    2a8: 0104d493  srli         x9, x9, 16
    2ac: 00a4f663  bgeu         x9, x10, 0x000002b8  # target 0x000002b8
    2b0: 0ff0000f  fence        0xf, 0xf
    2b4: fe1ff06f  jal          x0, 0x00000294  # target 0x00000294
loc_2b8:
    2b8: 0ff0000f  fence        0xf, 0xf
    2bc: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    2c0: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    2c4: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    2c8: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
    2cc: 00f2f493  andi         x9, x5, 15
    2d0: 00149493  slli         x9, x9, 1
    2d4: 0102f593  andi         x11, x5, 16
    2d8: 00559593  slli         x11, x11, 5
    2dc: 00b4e4b3  or           x9, x9, x11
    2e0: 1e02f593  andi         x11, x5, 480
    2e4: 00b4e4b3  or           x9, x9, x11
    2e8: 0092d593  srli         x11, x5, 9
    2ec: 00a59593  slli         x11, x11, 10
    2f0: 00b4e4b3  or           x9, x9, x11
    2f4: 00016537  lui          x10, 0x00016  # x10 = 0x00016000
    2f8: 7c050513  addi         x10, x10, 1984  # x10 = 0x000167c0
    2fc: 00950533  add          x10, x10, x9
    300: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
    304: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    308: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    30c: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    310: 00138393  addi         x7, x7, 1
    314: 01039393  slli         x7, x7, 16
    318: 0103d393  srli         x7, x7, 16
    31c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    320: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    324: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    328: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    32c: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    330: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    334: 0ff0000f  fence        0xf, 0xf
    338: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    33c: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    340: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    344: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    348: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    34c: 008383b3  add          x7, x7, x8
    350: 000144b7  lui          x9, 0x00014  # x9 = 0x00014000
    354: fc048493  addi         x9, x9, -64  # x9 = 0x00013fc0
    358: 0093e663  bltu         x7, x9, 0x00000364  # target 0x00000364
    35c: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    360: 40a383b3  sub          x7, x7, x10
loc_364:
    364: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    368: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    36c: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    370: 00128293  addi         x5, x5, 1
    374: f0dff06f  jal          x0, 0x00000280  # target 0x00000280
loc_378:
    378: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    37c: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    380: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    384: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    388: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    38c: 00520233  add          x4, x4, x5
    390: 00017337  lui          x6, 0x00017  # x6 = 0x00017000
    394: fc030313  addi         x6, x6, -64  # x6 = 0x00016fc0
    398: 00626863  bltu         x4, x6, 0x000003a8  # target 0x000003a8
    39c: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3a0: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    3a4: 40720233  sub          x4, x4, x7
loc_3a8:
    3a8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    3ac: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    3b0: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    3b4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    3b8: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    3bc: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    3c0: 00120213  addi         x4, x4, 1
    3c4: 01021213  slli         x4, x4, 16
    3c8: 01025213  srli         x4, x4, 16
    3cc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    3d0: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    3d4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    3d8: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    3dc: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    3e0: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    3e4: 0ff0000f  fence        0xf, 0xf
    3e8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    3ec: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
    3f0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880
    3f4: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_3f8:
    3f8: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    3fc: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    400: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    404: 40428333  sub          x6, x5, x4
    408: 01031313  slli         x6, x6, 16
    40c: 01035313  srli         x6, x6, 16
    410: 00737663  bgeu         x6, x7, 0x0000041c  # target 0x0000041c
    414: 0ff0000f  fence        0xf, 0xf
    418: fe1ff06f  jal          x0, 0x000003f8  # target 0x000003f8
loc_41c:
    41c: 0ff0000f  fence        0xf, 0xf
    420: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
    424: 95038393  addi         x7, x7, -1712  # x7 = 0x0000e950
    428: 0003a203  lw           x4, 0(x7)  # param dense_start; 0x0000e950
    42c: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
    430: 95438393  addi         x7, x7, -1708  # x7 = 0x0000e954
    434: 0003a303  lw           x6, 0(x7)  # param e2e_l0_gate_rows; 0x0000e954
    438: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    43c: 87c38393  addi         x7, x7, -1924  # x7 = 0xffb0087c · riscv_local_mem + 0x87c
    440: 0003a283  lw           x5, 0(x7)  # riscv_local_mem + 0x87c · 0xffb0087c
    444: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    448: 00030413  addi         x8, x6, 0
loc_44c:
    44c: 0483fa63  bgeu         x7, x8, 0x000004a0  # target 0x000004a0
    450: 007204b3  add          x9, x4, x7
    454: 00f3f513  andi         x10, x7, 15
    458: 00151513  slli         x10, x10, 1
    45c: 0103f693  andi         x13, x7, 16
    460: 00569693  slli         x13, x13, 5
    464: 00d56533  or           x10, x10, x13
    468: 1e03f693  andi         x13, x7, 480
    46c: 00d56533  or           x10, x10, x13
    470: 0093d693  srli         x13, x7, 9
    474: 00a69693  slli         x13, x13, 10
    478: 00d56533  or           x10, x10, x13
    47c: 00a28533  add          x10, x5, x10
    480: 00055603  lhu          x12, 0(x10)  # Address depends on runtime register values
    484: 00149593  slli         x11, x9, 1
    488: 0001b6b7  lui          x13, 0x0001b  # x13 = 0x0001b000
    48c: 7c068693  addi         x13, x13, 1984  # x13 = 0x0001b7c0
    490: 00d585b3  add          x11, x11, x13
    494: 00c59023  sh           x12, 0(x11)  # Address depends on runtime register values
    498: 00138393  addi         x7, x7, 1
    49c: fb1ff06f  jal          x0, 0x0000044c  # target 0x0000044c
loc_4a0:
    4a0: 1a8000ef  jal          x1, 0x00000648  # target 0x00000648; x1 = 0x000004a4
    4a4: 1c0000ef  jal          x1, 0x00000664  # target 0x00000664; x1 = 0x000004a8
    4a8: 00020393  addi         x7, x4, 0
    4ac: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    4b0: 95448493  addi         x9, x9, -1708  # x9 = 0x0000e954
    4b4: 0004a403  lw           x8, 0(x9)  # param e2e_l0_gate_rows; 0x0000e954
    4b8: 00440433  add          x8, x8, x4
loc_4bc:
    4bc: 00a3d493  srli         x9, x7, 10
    4c0: 00048f93  addi         x31, x9, 0
    4c4: 1bc000ef  jal          x1, 0x00000680  # target 0x00000680; x1 = 0x000004c8
    4c8: 000a8793  addi         x15, x21, 0
    4cc: 000b0813  addi         x16, x22, 0
    4d0: 00139513  slli         x10, x7, 1
    4d4: 0001b6b7  lui          x13, 0x0001b  # x13 = 0x0001b000
    4d8: 7c068693  addi         x13, x13, 1984  # x13 = 0x0001b7c0
    4dc: 00a686b3  add          x13, x13, x10
    4e0: 7ff57513  andi         x10, x10, 2047
    4e4: 00a78733  add          x14, x15, x10
    4e8: 00f3f593  andi         x11, x7, 15
    4ec: 01000613  addi         x12, x0, 16  # x12 = 0x00000010
    4f0: 40b605b3  sub          x11, x12, x11
    4f4: 40740633  sub          x12, x8, x7
    4f8: 00b67463  bgeu         x12, x11, 0x00000500  # target 0x00000500
    4fc: 00060593  addi         x11, x12, 0
loc_500:
    500: 00b383b3  add          x7, x7, x11
    504: 00159593  slli         x11, x11, 1
    508: 00068f93  addi         x31, x13, 0
    50c: 00070f13  addi         x30, x14, 0
    510: 00080e93  addi         x29, x16, 0
    514: 00058e13  addi         x28, x11, 0
loc_518:
    518: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    51c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    520: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    524: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    528: 015a6463  bltu         x20, x21, 0x00000530  # target 0x00000530
    52c: fedff06f  jal          x0, 0x00000518  # target 0x00000518
loc_530:
    530: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    534: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    538: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    53c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    540: 015a6463  bltu         x20, x21, 0x00000548  # target 0x00000548
    544: fedff06f  jal          x0, 0x00000530  # target 0x00000530
loc_548:
    548: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    54c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    550: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    554: 014a1a13  slli         x20, x20, 20
    558: 014a5a13  srli         x20, x20, 20
    55c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_560:
    560: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    564: 000b0463  beq          x22, x0, 0x0000056c  # target 0x0000056c
    568: ff9ff06f  jal          x0, 0x00000560  # target 0x00000560
loc_56c:
    56c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    570: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    574: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    578: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    57c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    580: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    584: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    588: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    58c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    590: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    594: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    598: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    59c: 03cba023  sw           x28, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write runtime value
    5a0: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    5a4: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    5a8: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    5ac: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    5b0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    5b4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    5b8: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_5bc:
    5bc: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    5c0: 000b0463  beq          x22, x0, 0x000005c8  # target 0x000005c8
    5c4: ff9ff06f  jal          x0, 0x000005bc  # target 0x000005bc
loc_5c8:
    5c8: ee83eae3  bltu         x7, x8, 0x000004bc  # target 0x000004bc
    5cc: 07c000ef  jal          x1, 0x00000648  # target 0x00000648; x1 = 0x000005d0
    5d0: 094000ef  jal          x1, 0x00000664  # target 0x00000664; x1 = 0x000005d4
    5d4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    5d8: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    5dc: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880
    5e0: 00120213  addi         x4, x4, 1
    5e4: 01021213  slli         x4, x4, 16
    5e8: 01025213  srli         x4, x4, 16
    5ec: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    5f0: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    5f4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    5f8: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    5fc: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    600: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    604: 0ff0000f  fence        0xf, 0xf
    608: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    60c: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    610: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    614: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    618: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    61c: 00520233  add          x4, x4, x5
    620: 0001b337  lui          x6, 0x0001b  # x6 = 0x0001b000
    624: 7c030313  addi         x6, x6, 1984  # x6 = 0x0001b7c0
    628: 00626863  bltu         x4, x6, 0x00000638  # target 0x00000638
    62c: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    630: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    634: 40720233  sub          x4, x4, x7
loc_638:
    638: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    63c: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    640: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    644: 0c00006f  jal          x0, 0x00000704  # target 0x00000704
loc_648:
    648: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    64c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    650: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    654: 000a0463  beq          x20, x0, 0x0000065c  # target 0x0000065c
    658: ff1ff06f  jal          x0, 0x00000648  # target 0x00000648
loc_65c:
    65c: 0ff0000f  fence        0xf, 0xf
    660: 00008067  jalr         x0, 0(x1)
loc_664:
    664: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    668: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    66c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    670: 000a0463  beq          x20, x0, 0x00000678  # target 0x00000678
    674: ff1ff06f  jal          x0, 0x00000664  # target 0x00000664
loc_678:
    678: 0ff0000f  fence        0xf, 0xf
    67c: 00008067  jalr         x0, 0(x1)
loc_680:
    680: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    684: 000aaa03  lw           x20, 0(x21)  # param e2e_hidden_dense; 0x0000078c
    688: 007a7d13  andi         x26, x20, 7
    68c: ff8a7a13  andi         x20, x20, -8
    690: 01af8ab3  add          x21, x31, x26
    694: 007afb93  andi         x23, x21, 7
    698: 003ada93  srli         x21, x21, 3
    69c: 00ba9a93  slli         x21, x21, 11
    6a0: 014a8ab3  add          x21, x21, x20
    6a4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000006a4
    6a8: 030b0b13  addi         x22, x22, 48  # x22 = 0x000006d4
    6ac: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    6b0: 95ce8e93  addi         x29, x29, -1700  # x29 = 0x0000e95c
    6b4: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e95c
    6b8: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    6bc: 03cd8db3  mul          x27, x27, x28
    6c0: 01bb0b33  add          x22, x22, x27
    6c4: 001b9b93  slli         x23, x23, 1
    6c8: 017b0b33  add          x22, x22, x23
    6cc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6d0: 00008067  jalr         x0, 0(x1)
    6d4: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6d8: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6dc: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6e0: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    6e4: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6e8: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6ec: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    6f0: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    6f4: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    6f8: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6fc: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    700: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    704:           j FW_NCRISC+4   # return to firmware, linked at install
