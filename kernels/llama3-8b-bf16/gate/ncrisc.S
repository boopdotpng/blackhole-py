# llama3 8b-bf16 decode: gate, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x7c0=e2e_x_b_decode_token, 0x7c4=e2e_l0_gate, 0x7c8=e2e_l0_up, 0x7cc=e2e_hidden_dense, 0x7d0=e2e_l0_post_norm, 0x8100=e2e_gate, 0x8104=e2e_l0_gate_row_start, 0x8108=e2e_up, 0x810c=e2e_l0_up_row_start, 0x8110=dense_start, 0x8114=e2e_l0_gate_rows, 0x8118=e2e_l0_up_rows, 0x811c=dram_port
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
      4: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
      8: 00094437  lui          x8, 0x00094  # x8 = 0x00094000
      c: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00094000
     10: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     14: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     18: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     20: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     24: 000972b7  lui          x5, 0x00097  # x5 = 0x00097000
     28: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x00097000
     2c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     30: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     34: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     38: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     3c: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     40: 000982b7  lui          x5, 0x00098  # x5 = 0x00098000
     44: 80028293  addi         x5, x5, -2048  # x5 = 0x00097800
     48: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x00097800
     4c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     50: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     54: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     58: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     5c: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     60: 0009c2b7  lui          x5, 0x0009c  # x5 = 0x0009c000
     64: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x0009c000
     68: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     6c: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     70: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00000000
     74: 00097237  lui          x4, 0x00097  # x4 = 0x00097000
     78: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_7c:
     7c: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     80: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     84: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     88: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     8c: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     90: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     94: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     98: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     9c: 02020213  addi         x4, x4, 32
     a0: ff828293  addi         x5, x5, -8
     a4: fc029ce3  bne          x5, x0, 0x0000007c  # target 0x0000007c
     a8: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
     ac: 11428293  addi         x5, x5, 276  # x5 = 0x00008114
     b0: 0002a203  lw           x4, 0(x5)  # param e2e_l0_gate_rows; 0x00008114
     b4: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     b8: 00020313  addi         x6, x4, 0
loc_bc:
     bc: 0e62f863  bgeu         x5, x6, 0x000001ac  # target 0x000001ac
     c0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     c4: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
     c8: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
     cc: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_d0:
     d0: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
     d4: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
     d8: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
     dc: 407404b3  sub          x9, x8, x7
     e0: 01049493  slli         x9, x9, 16
     e4: 0104d493  srli         x9, x9, 16
     e8: 00a4f663  bgeu         x9, x10, 0x000000f4  # target 0x000000f4
     ec: 0ff0000f  fence        0xf, 0xf
     f0: fe1ff06f  jal          x0, 0x000000d0  # target 0x000000d0
loc_f4:
     f4: 0ff0000f  fence        0xf, 0xf
     f8: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     fc: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    100: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    104: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
    108: 00f2f493  andi         x9, x5, 15
    10c: 00149493  slli         x9, x9, 1
    110: 0102f593  andi         x11, x5, 16
    114: 00559593  slli         x11, x11, 5
    118: 00b4e4b3  or           x9, x9, x11
    11c: 1e02f593  andi         x11, x5, 480
    120: 00b4e4b3  or           x9, x9, x11
    124: 0092d593  srli         x11, x5, 9
    128: 00a59593  slli         x11, x11, 10
    12c: 00b4e4b3  or           x9, x9, x11
    130: 00097537  lui          x10, 0x00097  # x10 = 0x00097000
    134: 00950533  add          x10, x10, x9
    138: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
    13c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    140: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    144: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    148: 00138393  addi         x7, x7, 1
    14c: 01039393  slli         x7, x7, 16
    150: 0103d393  srli         x7, x7, 16
    154: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    158: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    15c: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    160: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    164: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    168: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    16c: 0ff0000f  fence        0xf, 0xf
    170: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    174: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    178: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    17c: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    180: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    184: 008383b3  add          x7, x7, x8
    188: 000954b7  lui          x9, 0x00095  # x9 = 0x00095000
    18c: 0093e663  bltu         x7, x9, 0x00000198  # target 0x00000198
    190: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    194: 40a383b3  sub          x7, x7, x10
loc_198:
    198: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    19c: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    1a0: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    1a4: 00128293  addi         x5, x5, 1
    1a8: f15ff06f  jal          x0, 0x000000bc  # target 0x000000bc
loc_1ac:
    1ac: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1b0: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1b4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    1b8: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1bc: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    1c0: 00520233  add          x4, x4, x5
    1c4: 00098337  lui          x6, 0x00098  # x6 = 0x00098000
    1c8: 80030313  addi         x6, x6, -2048  # x6 = 0x00097800
    1cc: 00626863  bltu         x4, x6, 0x000001dc  # target 0x000001dc
    1d0: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1d4: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    1d8: 40720233  sub          x4, x4, x7
loc_1dc:
    1dc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1e0: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1e4: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    1e8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1ec: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    1f0: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    1f4: 00120213  addi         x4, x4, 1
    1f8: 01021213  slli         x4, x4, 16
    1fc: 01025213  srli         x4, x4, 16
    200: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    204: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    208: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    20c: ffb4b2b7  lui          x5, 0xffb4b  # x5 = 0xffb4b000
    210: 02828293  addi         x5, x5, 40  # x5 = 0xffb4b028
    214: 0042a023  sw           x4, 0(x5)  # 0xffb4b028; write runtime value
    218: 0ff0000f  fence        0xf, 0xf
    21c: 00098237  lui          x4, 0x00098  # x4 = 0x00098000
    220: 80020213  addi         x4, x4, -2048  # x4 = 0x00097800
    224: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_228:
    228: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
    22c: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
    230: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
    234: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
    238: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
    23c: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
    240: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
    244: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
    248: 02020213  addi         x4, x4, 32
    24c: ff828293  addi         x5, x5, -8
    250: fc029ce3  bne          x5, x0, 0x00000228  # target 0x00000228
    254: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    258: 11828293  addi         x5, x5, 280  # x5 = 0x00008118
    25c: 0002a203  lw           x4, 0(x5)  # param e2e_l0_up_rows; 0x00008118
    260: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    264: 00020313  addi         x6, x4, 0
loc_268:
    268: 0e62fa63  bgeu         x5, x6, 0x0000035c  # target 0x0000035c
    26c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    270: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
    274: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
    278: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_27c:
    27c: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
    280: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
    284: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
    288: 407404b3  sub          x9, x8, x7
    28c: 01049493  slli         x9, x9, 16
    290: 0104d493  srli         x9, x9, 16
    294: 00a4f663  bgeu         x9, x10, 0x000002a0  # target 0x000002a0
    298: 0ff0000f  fence        0xf, 0xf
    29c: fe1ff06f  jal          x0, 0x0000027c  # target 0x0000027c
loc_2a0:
    2a0: 0ff0000f  fence        0xf, 0xf
    2a4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    2a8: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    2ac: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    2b0: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
    2b4: 00f2f493  andi         x9, x5, 15
    2b8: 00149493  slli         x9, x9, 1
    2bc: 0102f593  andi         x11, x5, 16
    2c0: 00559593  slli         x11, x11, 5
    2c4: 00b4e4b3  or           x9, x9, x11
    2c8: 1e02f593  andi         x11, x5, 480
    2cc: 00b4e4b3  or           x9, x9, x11
    2d0: 0092d593  srli         x11, x5, 9
    2d4: 00a59593  slli         x11, x11, 10
    2d8: 00b4e4b3  or           x9, x9, x11
    2dc: 00098537  lui          x10, 0x00098  # x10 = 0x00098000
    2e0: 80050513  addi         x10, x10, -2048  # x10 = 0x00097800
    2e4: 00950533  add          x10, x10, x9
    2e8: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
    2ec: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    2f0: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    2f4: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    2f8: 00138393  addi         x7, x7, 1
    2fc: 01039393  slli         x7, x7, 16
    300: 0103d393  srli         x7, x7, 16
    304: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    308: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    30c: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    310: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    314: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    318: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    31c: 0ff0000f  fence        0xf, 0xf
    320: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    324: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    328: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    32c: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    330: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    334: 008383b3  add          x7, x7, x8
    338: 000954b7  lui          x9, 0x00095  # x9 = 0x00095000
    33c: 0093e663  bltu         x7, x9, 0x00000348  # target 0x00000348
    340: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    344: 40a383b3  sub          x7, x7, x10
loc_348:
    348: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    34c: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    350: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    354: 00128293  addi         x5, x5, 1
    358: f11ff06f  jal          x0, 0x00000268  # target 0x00000268
loc_35c:
    35c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    360: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    364: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    368: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    36c: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    370: 00520233  add          x4, x4, x5
    374: 00098337  lui          x6, 0x00098  # x6 = 0x00098000
    378: 00626863  bltu         x4, x6, 0x00000388  # target 0x00000388
    37c: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    380: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    384: 40720233  sub          x4, x4, x7
loc_388:
    388: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    38c: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    390: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    394: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    398: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    39c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    3a0: 00120213  addi         x4, x4, 1
    3a4: 01021213  slli         x4, x4, 16
    3a8: 01025213  srli         x4, x4, 16
    3ac: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    3b0: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    3b4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    3b8: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    3bc: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    3c0: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    3c4: 0ff0000f  fence        0xf, 0xf
    3c8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    3cc: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
    3d0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880
    3d4: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_3d8:
    3d8: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    3dc: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    3e0: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    3e4: 40428333  sub          x6, x5, x4
    3e8: 01031313  slli         x6, x6, 16
    3ec: 01035313  srli         x6, x6, 16
    3f0: 00737663  bgeu         x6, x7, 0x000003fc  # target 0x000003fc
    3f4: 0ff0000f  fence        0xf, 0xf
    3f8: fe1ff06f  jal          x0, 0x000003d8  # target 0x000003d8
loc_3fc:
    3fc: 0ff0000f  fence        0xf, 0xf
    400: 000083b7  lui          x7, 0x00008  # x7 = 0x00008000
    404: 11038393  addi         x7, x7, 272  # x7 = 0x00008110
    408: 0003a203  lw           x4, 0(x7)  # param dense_start; 0x00008110
    40c: 000083b7  lui          x7, 0x00008  # x7 = 0x00008000
    410: 11438393  addi         x7, x7, 276  # x7 = 0x00008114
    414: 0003a303  lw           x6, 0(x7)  # param e2e_l0_gate_rows; 0x00008114
    418: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    41c: 87c38393  addi         x7, x7, -1924  # x7 = 0xffb0087c · riscv_local_mem + 0x87c
    420: 0003a283  lw           x5, 0(x7)  # riscv_local_mem + 0x87c · 0xffb0087c
    424: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    428: 00030413  addi         x8, x6, 0
loc_42c:
    42c: 0483fa63  bgeu         x7, x8, 0x00000480  # target 0x00000480
    430: 007204b3  add          x9, x4, x7
    434: 00f3f513  andi         x10, x7, 15
    438: 00151513  slli         x10, x10, 1
    43c: 0103f693  andi         x13, x7, 16
    440: 00569693  slli         x13, x13, 5
    444: 00d56533  or           x10, x10, x13
    448: 1e03f693  andi         x13, x7, 480
    44c: 00d56533  or           x10, x10, x13
    450: 0093d693  srli         x13, x7, 9
    454: 00a69693  slli         x13, x13, 10
    458: 00d56533  or           x10, x10, x13
    45c: 00a28533  add          x10, x5, x10
    460: 00055603  lhu          x12, 0(x10)  # Address depends on runtime register values
    464: 00149593  slli         x11, x9, 1
    468: 0009d6b7  lui          x13, 0x0009d  # x13 = 0x0009d000
    46c: 80068693  addi         x13, x13, -2048  # x13 = 0x0009c800
    470: 00d585b3  add          x11, x11, x13
    474: 00c59023  sh           x12, 0(x11)  # Address depends on runtime register values
    478: 00138393  addi         x7, x7, 1
    47c: fb1ff06f  jal          x0, 0x0000042c  # target 0x0000042c
loc_480:
    480: 1a8000ef  jal          x1, 0x00000628  # target 0x00000628; x1 = 0x00000484
    484: 1c0000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x00000488
    488: 00020393  addi         x7, x4, 0
    48c: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    490: 11448493  addi         x9, x9, 276  # x9 = 0x00008114
    494: 0004a403  lw           x8, 0(x9)  # param e2e_l0_gate_rows; 0x00008114
    498: 00440433  add          x8, x8, x4
loc_49c:
    49c: 00a3d493  srli         x9, x7, 10
    4a0: 00048f93  addi         x31, x9, 0
    4a4: 1bc000ef  jal          x1, 0x00000660  # target 0x00000660; x1 = 0x000004a8
    4a8: 000a8793  addi         x15, x21, 0
    4ac: 000b0813  addi         x16, x22, 0
    4b0: 00139513  slli         x10, x7, 1
    4b4: 0009d6b7  lui          x13, 0x0009d  # x13 = 0x0009d000
    4b8: 80068693  addi         x13, x13, -2048  # x13 = 0x0009c800
    4bc: 00a686b3  add          x13, x13, x10
    4c0: 7ff57513  andi         x10, x10, 2047
    4c4: 00a78733  add          x14, x15, x10
    4c8: 00f3f593  andi         x11, x7, 15
    4cc: 01000613  addi         x12, x0, 16  # x12 = 0x00000010
    4d0: 40b605b3  sub          x11, x12, x11
    4d4: 40740633  sub          x12, x8, x7
    4d8: 00b67463  bgeu         x12, x11, 0x000004e0  # target 0x000004e0
    4dc: 00060593  addi         x11, x12, 0
loc_4e0:
    4e0: 00b383b3  add          x7, x7, x11
    4e4: 00159593  slli         x11, x11, 1
    4e8: 00068f93  addi         x31, x13, 0
    4ec: 00070f13  addi         x30, x14, 0
    4f0: 00080e93  addi         x29, x16, 0
    4f4: 00058e13  addi         x28, x11, 0
loc_4f8:
    4f8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    4fc: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    500: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    504: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    508: 015a6463  bltu         x20, x21, 0x00000510  # target 0x00000510
    50c: fedff06f  jal          x0, 0x000004f8  # target 0x000004f8
loc_510:
    510: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    514: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    518: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    51c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    520: 015a6463  bltu         x20, x21, 0x00000528  # target 0x00000528
    524: fedff06f  jal          x0, 0x00000510  # target 0x00000510
loc_528:
    528: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    52c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    530: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    534: 014a1a13  slli         x20, x20, 20
    538: 014a5a13  srli         x20, x20, 20
    53c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_540:
    540: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    544: 000b0463  beq          x22, x0, 0x0000054c  # target 0x0000054c
    548: ff9ff06f  jal          x0, 0x00000540  # target 0x00000540
loc_54c:
    54c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    550: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    554: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    558: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    55c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    560: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    564: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    568: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    56c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    570: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    574: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    578: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    57c: 03cba023  sw           x28, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write runtime value
    580: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    584: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    588: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    58c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    590: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    594: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    598: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_59c:
    59c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    5a0: 000b0463  beq          x22, x0, 0x000005a8  # target 0x000005a8
    5a4: ff9ff06f  jal          x0, 0x0000059c  # target 0x0000059c
loc_5a8:
    5a8: ee83eae3  bltu         x7, x8, 0x0000049c  # target 0x0000049c
    5ac: 07c000ef  jal          x1, 0x00000628  # target 0x00000628; x1 = 0x000005b0
    5b0: 094000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x000005b4
    5b4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    5b8: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    5bc: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880
    5c0: 00120213  addi         x4, x4, 1
    5c4: 01021213  slli         x4, x4, 16
    5c8: 01025213  srli         x4, x4, 16
    5cc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    5d0: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    5d4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    5d8: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    5dc: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    5e0: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    5e4: 0ff0000f  fence        0xf, 0xf
    5e8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    5ec: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    5f0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    5f4: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5f8: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    5fc: 00520233  add          x4, x4, x5
    600: 0009d337  lui          x6, 0x0009d  # x6 = 0x0009d000
    604: 80030313  addi         x6, x6, -2048  # x6 = 0x0009c800
    608: 00626863  bltu         x4, x6, 0x00000618  # target 0x00000618
    60c: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    610: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    614: 40720233  sub          x4, x4, x7
loc_618:
    618: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    61c: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    620: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    624: 0c00006f  jal          x0, 0x000006e4  # target 0x000006e4
loc_628:
    628: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    62c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    630: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    634: 000a0463  beq          x20, x0, 0x0000063c  # target 0x0000063c
    638: ff1ff06f  jal          x0, 0x00000628  # target 0x00000628
loc_63c:
    63c: 0ff0000f  fence        0xf, 0xf
    640: 00008067  jalr         x0, 0(x1)
loc_644:
    644: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    648: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    64c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    650: 000a0463  beq          x20, x0, 0x00000658  # target 0x00000658
    654: ff1ff06f  jal          x0, 0x00000644  # target 0x00000644
loc_658:
    658: 0ff0000f  fence        0xf, 0xf
    65c: 00008067  jalr         x0, 0(x1)
loc_660:
    660: 7cc00a93  addi         x21, x0, 1996  # x21 = 0x000007cc
    664: 000aaa03  lw           x20, 0(x21)  # param e2e_hidden_dense; 0x000007cc
    668: 007a7d13  andi         x26, x20, 7
    66c: ff8a7a13  andi         x20, x20, -8
    670: 01af8ab3  add          x21, x31, x26
    674: 007afb93  andi         x23, x21, 7
    678: 003ada93  srli         x21, x21, 3
    67c: 00ba9a93  slli         x21, x21, 11
    680: 014a8ab3  add          x21, x21, x20
    684: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000684
    688: 030b0b13  addi         x22, x22, 48  # x22 = 0x000006b4
    68c: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    690: 11ce8e93  addi         x29, x29, 284  # x29 = 0x0000811c
    694: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000811c
    698: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    69c: 03cd8db3  mul          x27, x27, x28
    6a0: 01bb0b33  add          x22, x22, x27
    6a4: 001b9b93  slli         x23, x23, 1
    6a8: 017b0b33  add          x22, x22, x23
    6ac: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6b0: 00008067  jalr         x0, 0(x1)
    6b4: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6b8: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6bc: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6c0: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    6c4: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6c8: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6cc: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    6d0: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    6d4: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    6d8: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6dc: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    6e0: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    6e4:           j FW_NCRISC+4   # return to firmware, linked at install
