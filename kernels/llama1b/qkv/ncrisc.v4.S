# llama3 1B decode: qkv, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/export_llama1b.py.
# cores (16): 4,4 7,4 12,4 2,5 5,5 10,5 13,5 2,6 5,6 10,6 13,6 2,7 5,7 10,7 13,7 2,8
# params: 0x7c0=e2e_x_a_decode_token, 0x7c4=e2e_l0_q, 0x7c8=e2e_l0_k, 0x7cc=e2e_l0_v, 0x7d0=e2e_l0_input_norm, 0x8080=e2e_q_compact, 0x8084=e2e_l0_q_row_start, 0x8088=e2e_k_compact, 0x808c=e2e_l0_k_row_start, 0x8090=e2e_v_compact, 0x8094=e2e_l0_v_row_start
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama1b.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
      4: 86430313  addi         x6, x6, -1948  # x6 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000923b7  lui          x7, 0x00092  # x7 = 0x00092000
      c: 00732023  sw           x7, 0(x6)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00092000
     10: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
     14: 86830313  addi         x6, x6, -1944  # x6 = 0xffb00868 · riscv_local_mem + 0x868
     18: 00032023  sw           x0, 0(x6)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: 00094237  lui          x4, 0x00094  # x4 = 0x00094000
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
     50: 00000213  addi         x4, x0, 0  # x4 = 0x00000000
     54: 01700293  addi         x5, x0, 23  # x5 = 0x00000017
loc_58:
     58: 0e527863  bgeu         x4, x5, 0x00000148  # target 0x00000148
     5c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     60: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
     64: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
     68: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
loc_6c:
     6c: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
     70: 02850513  addi         x10, x10, 40  # x10 = 0xffb49028
     74: 00055383  lhu          x7, 0(x10)  # 0xffb49028
     78: 40638433  sub          x8, x7, x6
     7c: 01041413  slli         x8, x8, 16
     80: 01045413  srli         x8, x8, 16
     84: 00947663  bgeu         x8, x9, 0x00000090  # target 0x00000090
     88: 0ff0000f  fence        0xf, 0xf
     8c: fe1ff06f  jal          x0, 0x0000006c  # target 0x0000006c
loc_90:
     90: 0ff0000f  fence        0xf, 0xf
     94: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     98: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
     9c: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
     a0: 00035383  lhu          x7, 0(x6)  # Address depends on runtime register values
     a4: 00f27413  andi         x8, x4, 15
     a8: 00141413  slli         x8, x8, 1
     ac: 01027513  andi         x10, x4, 16
     b0: 00551513  slli         x10, x10, 5
     b4: 00a46433  or           x8, x8, x10
     b8: 1e027513  andi         x10, x4, 480
     bc: 00a46433  or           x8, x8, x10
     c0: 00925513  srli         x10, x4, 9
     c4: 00a51513  slli         x10, x10, 10
     c8: 00a46433  or           x8, x8, x10
     cc: 000944b7  lui          x9, 0x00094  # x9 = 0x00094000
     d0: 008484b3  add          x9, x9, x8
     d4: 00749023  sh           x7, 0(x9)  # Address depends on runtime register values
     d8: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     dc: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     e0: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868
     e4: 00130313  addi         x6, x6, 1
     e8: 01031313  slli         x6, x6, 16
     ec: 01035313  srli         x6, x6, 16
     f0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     f4: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     f8: 0063a023  sw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
     fc: ffb493b7  lui          x7, 0xffb49  # x7 = 0xffb49000
    100: 02038393  addi         x7, x7, 32  # x7 = 0xffb49020
    104: 0063a023  sw           x6, 0(x7)  # 0xffb49020; write runtime value
    108: 0ff0000f  fence        0xf, 0xf
    10c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    110: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    114: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
    118: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    11c: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    120: 00730333  add          x6, x6, x7
    124: 00093437  lui          x8, 0x00093  # x8 = 0x00093000
    128: 00836663  bltu         x6, x8, 0x00000134  # target 0x00000134
    12c: 000014b7  lui          x9, 0x00001  # x9 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    130: 40930333  sub          x6, x6, x9
loc_134:
    134: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    138: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    13c: 00652023  sw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    140: 00120213  addi         x4, x4, 1
    144: f15ff06f  jal          x0, 0x00000058  # target 0x00000058
loc_148:
    148: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    14c: 2f4000ef  jal          x1, 0x00000440  # target 0x00000440; x1 = 0x00000150
    150: 000a8213  addi         x4, x21, 0
    154: 000b0293  addi         x5, x22, 0
    158: 338000ef  jal          x1, 0x00000490  # target 0x00000490; x1 = 0x0000015c
    15c: 350000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x00000160
    160: 00094fb7  lui          x31, 0x00094  # x31 = 0x00094000
    164: 00020f13  addi         x30, x4, 0
    168: 00028e93  addi         x29, x5, 0
    16c: 35c000ef  jal          x1, 0x000004c8  # target 0x000004c8; x1 = 0x00000170
    170: 320000ef  jal          x1, 0x00000490  # target 0x00000490; x1 = 0x00000174
    174: 338000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x00000178
    178: 00095237  lui          x4, 0x00095  # x4 = 0x00095000
    17c: 80020213  addi         x4, x4, -2048  # x4 = 0x00094800
    180: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_184:
    184: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
    188: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
    18c: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
    190: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
    194: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
    198: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
    19c: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
    1a0: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
    1a4: 02020213  addi         x4, x4, 32
    1a8: ff828293  addi         x5, x5, -8
    1ac: fc029ce3  bne          x5, x0, 0x00000184  # target 0x00000184
    1b0: 00000213  addi         x4, x0, 0  # x4 = 0x00000000
    1b4: 00600293  addi         x5, x0, 6  # x5 = 0x00000006
loc_1b8:
    1b8: 0e527a63  bgeu         x4, x5, 0x000002ac  # target 0x000002ac
    1bc: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1c0: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
    1c4: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
    1c8: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
loc_1cc:
    1cc: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
    1d0: 02850513  addi         x10, x10, 40  # x10 = 0xffb49028
    1d4: 00055383  lhu          x7, 0(x10)  # 0xffb49028
    1d8: 40638433  sub          x8, x7, x6
    1dc: 01041413  slli         x8, x8, 16
    1e0: 01045413  srli         x8, x8, 16
    1e4: 00947663  bgeu         x8, x9, 0x000001f0  # target 0x000001f0
    1e8: 0ff0000f  fence        0xf, 0xf
    1ec: fe1ff06f  jal          x0, 0x000001cc  # target 0x000001cc
loc_1f0:
    1f0: 0ff0000f  fence        0xf, 0xf
    1f4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1f8: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    1fc: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
    200: 00035383  lhu          x7, 0(x6)  # Address depends on runtime register values
    204: 00f27413  andi         x8, x4, 15
    208: 00141413  slli         x8, x8, 1
    20c: 01027513  andi         x10, x4, 16
    210: 00551513  slli         x10, x10, 5
    214: 00a46433  or           x8, x8, x10
    218: 1e027513  andi         x10, x4, 480
    21c: 00a46433  or           x8, x8, x10
    220: 00925513  srli         x10, x4, 9
    224: 00a51513  slli         x10, x10, 10
    228: 00a46433  or           x8, x8, x10
    22c: 000954b7  lui          x9, 0x00095  # x9 = 0x00095000
    230: 80048493  addi         x9, x9, -2048  # x9 = 0x00094800
    234: 008484b3  add          x9, x9, x8
    238: 00749023  sh           x7, 0(x9)  # Address depends on runtime register values
    23c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    240: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
    244: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868
    248: 00130313  addi         x6, x6, 1
    24c: 01031313  slli         x6, x6, 16
    250: 01035313  srli         x6, x6, 16
    254: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    258: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
    25c: 0063a023  sw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    260: ffb493b7  lui          x7, 0xffb49  # x7 = 0xffb49000
    264: 02038393  addi         x7, x7, 32  # x7 = 0xffb49020
    268: 0063a023  sw           x6, 0(x7)  # 0xffb49020; write runtime value
    26c: 0ff0000f  fence        0xf, 0xf
    270: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    274: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    278: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
    27c: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    280: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    284: 00730333  add          x6, x6, x7
    288: 00093437  lui          x8, 0x00093  # x8 = 0x00093000
    28c: 00836663  bltu         x6, x8, 0x00000298  # target 0x00000298
    290: 000014b7  lui          x9, 0x00001  # x9 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    294: 40930333  sub          x6, x6, x9
loc_298:
    298: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    29c: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    2a0: 00652023  sw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    2a4: 00120213  addi         x4, x4, 1
    2a8: f11ff06f  jal          x0, 0x000001b8  # target 0x000001b8
loc_2ac:
    2ac: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    2b0: 2d4000ef  jal          x1, 0x00000584  # target 0x00000584; x1 = 0x000002b4
    2b4: 000a8213  addi         x4, x21, 0
    2b8: 000b0293  addi         x5, x22, 0
    2bc: 1d4000ef  jal          x1, 0x00000490  # target 0x00000490; x1 = 0x000002c0
    2c0: 1ec000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x000002c4
    2c4: 00095fb7  lui          x31, 0x00095  # x31 = 0x00095000
    2c8: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00094800
    2cc: 00020f13  addi         x30, x4, 0
    2d0: 00028e93  addi         x29, x5, 0
    2d4: 1f4000ef  jal          x1, 0x000004c8  # target 0x000004c8; x1 = 0x000002d8
    2d8: 1b8000ef  jal          x1, 0x00000490  # target 0x00000490; x1 = 0x000002dc
    2dc: 1d0000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x000002e0
    2e0: 00095237  lui          x4, 0x00095  # x4 = 0x00095000
    2e4: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_2e8:
    2e8: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
    2ec: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
    2f0: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
    2f4: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
    2f8: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
    2fc: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
    300: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
    304: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
    308: 02020213  addi         x4, x4, 32
    30c: ff828293  addi         x5, x5, -8
    310: fc029ce3  bne          x5, x0, 0x000002e8  # target 0x000002e8
    314: 00000213  addi         x4, x0, 0  # x4 = 0x00000000
    318: 00600293  addi         x5, x0, 6  # x5 = 0x00000006
loc_31c:
    31c: 0e527863  bgeu         x4, x5, 0x0000040c  # target 0x0000040c
    320: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    324: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
    328: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
    32c: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
loc_330:
    330: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
    334: 02850513  addi         x10, x10, 40  # x10 = 0xffb49028
    338: 00055383  lhu          x7, 0(x10)  # 0xffb49028
    33c: 40638433  sub          x8, x7, x6
    340: 01041413  slli         x8, x8, 16
    344: 01045413  srli         x8, x8, 16
    348: 00947663  bgeu         x8, x9, 0x00000354  # target 0x00000354
    34c: 0ff0000f  fence        0xf, 0xf
    350: fe1ff06f  jal          x0, 0x00000330  # target 0x00000330
loc_354:
    354: 0ff0000f  fence        0xf, 0xf
    358: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    35c: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    360: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
    364: 00035383  lhu          x7, 0(x6)  # Address depends on runtime register values
    368: 00f27413  andi         x8, x4, 15
    36c: 00141413  slli         x8, x8, 1
    370: 01027513  andi         x10, x4, 16
    374: 00551513  slli         x10, x10, 5
    378: 00a46433  or           x8, x8, x10
    37c: 1e027513  andi         x10, x4, 480
    380: 00a46433  or           x8, x8, x10
    384: 00925513  srli         x10, x4, 9
    388: 00a51513  slli         x10, x10, 10
    38c: 00a46433  or           x8, x8, x10
    390: 000954b7  lui          x9, 0x00095  # x9 = 0x00095000
    394: 008484b3  add          x9, x9, x8
    398: 00749023  sh           x7, 0(x9)  # Address depends on runtime register values
    39c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    3a0: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
    3a4: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868
    3a8: 00130313  addi         x6, x6, 1
    3ac: 01031313  slli         x6, x6, 16
    3b0: 01035313  srli         x6, x6, 16
    3b4: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    3b8: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
    3bc: 0063a023  sw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    3c0: ffb493b7  lui          x7, 0xffb49  # x7 = 0xffb49000
    3c4: 02038393  addi         x7, x7, 32  # x7 = 0xffb49020
    3c8: 0063a023  sw           x6, 0(x7)  # 0xffb49020; write runtime value
    3cc: 0ff0000f  fence        0xf, 0xf
    3d0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3d4: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    3d8: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
    3dc: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3e0: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    3e4: 00730333  add          x6, x6, x7
    3e8: 00093437  lui          x8, 0x00093  # x8 = 0x00093000
    3ec: 00836663  bltu         x6, x8, 0x000003f8  # target 0x000003f8
    3f0: 000014b7  lui          x9, 0x00001  # x9 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3f4: 40930333  sub          x6, x6, x9
loc_3f8:
    3f8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3fc: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    400: 00652023  sw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    404: 00120213  addi         x4, x4, 1
    408: f15ff06f  jal          x0, 0x0000031c  # target 0x0000031c
loc_40c:
    40c: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    410: 1c4000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x00000414
    414: 000a8213  addi         x4, x21, 0
    418: 000b0293  addi         x5, x22, 0
    41c: 074000ef  jal          x1, 0x00000490  # target 0x00000490; x1 = 0x00000420
    420: 08c000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x00000424
    424: 00095fb7  lui          x31, 0x00095  # x31 = 0x00095000
    428: 00020f13  addi         x30, x4, 0
    42c: 00028e93  addi         x29, x5, 0
    430: 098000ef  jal          x1, 0x000004c8  # target 0x000004c8; x1 = 0x00000434
    434: 05c000ef  jal          x1, 0x00000490  # target 0x00000490; x1 = 0x00000438
    438: 074000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x0000043c
    43c: 1e80006f  jal          x0, 0x00000624  # target 0x00000624
loc_440:
    440: 00008ab7  lui          x21, 0x00008  # x21 = 0x00008000
    444: 080a8a93  addi         x21, x21, 128  # x21 = 0x00008080
    448: 000aaa03  lw           x20, 0(x21)  # param e2e_q_compact; 0x00008080
    44c: 007a7d13  andi         x26, x20, 7
    450: ff8a7a13  andi         x20, x20, -8
    454: 01af8ab3  add          x21, x31, x26
    458: 007afb93  andi         x23, x21, 7
    45c: 003ada93  srli         x21, x21, 3
    460: 00ba9a93  slli         x21, x21, 11
    464: 014a8ab3  add          x21, x21, x20
    468: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000468
    46c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000480
    470: 001b9b93  slli         x23, x23, 1
    474: 017b0b33  add          x22, x22, x23
    478: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    47c: 00008067  jalr         x0, 0(x1)
    480: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    484: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    488: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    48c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_490:
    490: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    494: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    498: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    49c: 000a0463  beq          x20, x0, 0x000004a4  # target 0x000004a4
    4a0: ff1ff06f  jal          x0, 0x00000490  # target 0x00000490
loc_4a4:
    4a4: 0ff0000f  fence        0xf, 0xf
    4a8: 00008067  jalr         x0, 0(x1)
loc_4ac:
    4ac: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    4b0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    4b4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    4b8: 000a0463  beq          x20, x0, 0x000004c0  # target 0x000004c0
    4bc: ff1ff06f  jal          x0, 0x000004ac  # target 0x000004ac
loc_4c0:
    4c0: 0ff0000f  fence        0xf, 0xf
    4c4: 00008067  jalr         x0, 0(x1)
loc_4c8:
    4c8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    4cc: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    4d0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    4d4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    4d8: 015a6463  bltu         x20, x21, 0x000004e0  # target 0x000004e0
    4dc: fedff06f  jal          x0, 0x000004c8  # target 0x000004c8
loc_4e0:
    4e0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    4e4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    4e8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    4ec: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    4f0: 015a6463  bltu         x20, x21, 0x000004f8  # target 0x000004f8
    4f4: fedff06f  jal          x0, 0x000004e0  # target 0x000004e0
loc_4f8:
    4f8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    4fc: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    500: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    504: 014a1a13  slli         x20, x20, 20
    508: 014a5a13  srli         x20, x20, 20
    50c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_510:
    510: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    514: 000b0463  beq          x22, x0, 0x0000051c  # target 0x0000051c
    518: ff9ff06f  jal          x0, 0x00000510  # target 0x00000510
loc_51c:
    51c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    520: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    524: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    528: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    52c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    530: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    534: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    538: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    53c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    540: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    544: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    548: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    54c: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    550: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    554: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    558: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    55c: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    560: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    564: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    568: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    56c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    570: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_574:
    574: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    578: 000b0463  beq          x22, x0, 0x00000580  # target 0x00000580
    57c: ff9ff06f  jal          x0, 0x00000574  # target 0x00000574
loc_580:
    580: 00008067  jalr         x0, 0(x1)
loc_584:
    584: 00008ab7  lui          x21, 0x00008  # x21 = 0x00008000
    588: 088a8a93  addi         x21, x21, 136  # x21 = 0x00008088
    58c: 000aaa03  lw           x20, 0(x21)  # param e2e_k_compact; 0x00008088
    590: 007a7d13  andi         x26, x20, 7
    594: ff8a7a13  andi         x20, x20, -8
    598: 01af8ab3  add          x21, x31, x26
    59c: 007afb93  andi         x23, x21, 7
    5a0: 003ada93  srli         x21, x21, 3
    5a4: 00ba9a93  slli         x21, x21, 11
    5a8: 014a8ab3  add          x21, x21, x20
    5ac: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005ac
    5b0: 018b0b13  addi         x22, x22, 24  # x22 = 0x000005c4
    5b4: 001b9b93  slli         x23, x23, 1
    5b8: 017b0b33  add          x22, x22, x23
    5bc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    5c0: 00008067  jalr         x0, 0(x1)
    5c4: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5c8: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5cc: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    5d0: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_5d4:
    5d4: 00008ab7  lui          x21, 0x00008  # x21 = 0x00008000
    5d8: 090a8a93  addi         x21, x21, 144  # x21 = 0x00008090
    5dc: 000aaa03  lw           x20, 0(x21)  # param e2e_v_compact; 0x00008090
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
    614: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    618: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    61c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    620: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    624:           j FW_NCRISC+4   # return to firmware, linked at install
