# llama3 8b-bf16 decode: gate, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x7c0=e2e_x_b_decode_token, 0x7c4=e2e_l0_gate, 0x7c8=e2e_l0_up, 0x7cc=e2e_hidden_dense, 0x7d0=e2e_l0_post_norm, 0x8100=e2e_gate, 0x8104=e2e_l0_gate_row_start, 0x8108=e2e_up, 0x810c=e2e_l0_up_row_start, 0x8110=dense_start, 0x8114=e2e_l0_gate_rows, 0x8118=e2e_l0_up_rows, 0x811c=dram_port
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000982b7  lui          x5, 0x00098  # x5 = 0x00098000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00098000
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
     44: ffb4d4b7  lui          x9, 0xffb4d  # x9 = 0xffb4d000
     48: 02048493  addi         x9, x9, 32  # x9 = 0xffb4d020
     4c: 0004d283  lhu          x5, 0(x9)  # 0xffb4d020
     50: 40520333  sub          x6, x4, x5
     54: 01031313  slli         x6, x6, 16
     58: 01035313  srli         x6, x6, 16
     5c: 00800393  addi         x7, x0, 8  # x7 = 0x00000008
     60: 406383b3  sub          x7, x7, x6
     64: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
     68: 0083f663  bgeu         x7, x8, 0x00000074  # target 0x00000074
     6c: 0ff0000f  fence        0xf, 0xf
     70: fd5ff06f  jal          x0, 0x00000044  # target 0x00000044
loc_74:
     74: 0ff0000f  fence        0xf, 0xf
     78: 3d4000ef  jal          x1, 0x0000044c  # target 0x0000044c; x1 = 0x0000007c
     7c: 3ec000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000080
     80: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     84: 400000ef  jal          x1, 0x00000484  # target 0x00000484; x1 = 0x00000088
     88: 000a8213  addi         x4, x21, 0
     8c: 000b0293  addi         x5, x22, 0
     90: 00020f93  addi         x31, x4, 0
     94: 00028f13  addi         x30, x5, 0
     98: 00098eb7  lui          x29, 0x00098  # x29 = 0x00098000
     9c: 46c000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x000000a0
     a0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     a4: 3e0000ef  jal          x1, 0x00000484  # target 0x00000484; x1 = 0x000000a8
     a8: 000a8213  addi         x4, x21, 0
     ac: 000b0293  addi         x5, x22, 0
     b0: 00020f93  addi         x31, x4, 0
     b4: 00028f13  addi         x30, x5, 0
     b8: 00099eb7  lui          x29, 0x00099  # x29 = 0x00099000
     bc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00098800
     c0: 448000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x000000c4
     c4: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     c8: 3bc000ef  jal          x1, 0x00000484  # target 0x00000484; x1 = 0x000000cc
     cc: 000a8213  addi         x4, x21, 0
     d0: 000b0293  addi         x5, x22, 0
     d4: 00020f93  addi         x31, x4, 0
     d8: 00028f13  addi         x30, x5, 0
     dc: 00099eb7  lui          x29, 0x00099  # x29 = 0x00099000
     e0: 428000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x000000e4
     e4: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     e8: 39c000ef  jal          x1, 0x00000484  # target 0x00000484; x1 = 0x000000ec
     ec: 000a8213  addi         x4, x21, 0
     f0: 000b0293  addi         x5, x22, 0
     f4: 00020f93  addi         x31, x4, 0
     f8: 00028f13  addi         x30, x5, 0
     fc: 0009aeb7  lui          x29, 0x0009a  # x29 = 0x0009a000
    100: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00099800
    104: 404000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000108
    108: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    10c: 4a0000ef  jal          x1, 0x000005ac  # target 0x000005ac; x1 = 0x00000110
    110: 000a8213  addi         x4, x21, 0
    114: 000b0293  addi         x5, x22, 0
    118: 00020f93  addi         x31, x4, 0
    11c: 00028f13  addi         x30, x5, 0
    120: 0009aeb7  lui          x29, 0x0009a  # x29 = 0x0009a000
    124: 3e4000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000128
    128: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    12c: 480000ef  jal          x1, 0x000005ac  # target 0x000005ac; x1 = 0x00000130
    130: 000a8213  addi         x4, x21, 0
    134: 000b0293  addi         x5, x22, 0
    138: 00020f93  addi         x31, x4, 0
    13c: 00028f13  addi         x30, x5, 0
    140: 0009beb7  lui          x29, 0x0009b  # x29 = 0x0009b000
    144: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009a800
    148: 3c0000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x0000014c
    14c: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    150: 45c000ef  jal          x1, 0x000005ac  # target 0x000005ac; x1 = 0x00000154
    154: 000a8213  addi         x4, x21, 0
    158: 000b0293  addi         x5, x22, 0
    15c: 00020f93  addi         x31, x4, 0
    160: 00028f13  addi         x30, x5, 0
    164: 0009beb7  lui          x29, 0x0009b  # x29 = 0x0009b000
    168: 3a0000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x0000016c
    16c: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    170: 43c000ef  jal          x1, 0x000005ac  # target 0x000005ac; x1 = 0x00000174
    174: 000a8213  addi         x4, x21, 0
    178: 000b0293  addi         x5, x22, 0
    17c: 00020f93  addi         x31, x4, 0
    180: 00028f13  addi         x30, x5, 0
    184: 0009ceb7  lui          x29, 0x0009c  # x29 = 0x0009c000
    188: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009b800
    18c: 37c000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000190
    190: 2d8000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000194
    194: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    198: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    19c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    1a0: 000042b7  lui          x5, 0x00004  # x5 = 0x00004000
    1a4: 00520233  add          x4, x4, x5
    1a8: 0009c337  lui          x6, 0x0009c  # x6 = 0x0009c000
    1ac: 00626663  bltu         x4, x6, 0x000001b8  # target 0x000001b8
    1b0: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    1b4: 40720233  sub          x4, x4, x7
loc_1b8:
    1b8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1bc: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1c0: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1c4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1c8: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1cc: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    1d0: 00820213  addi         x4, x4, 8
    1d4: 01021213  slli         x4, x4, 16
    1d8: 01025213  srli         x4, x4, 16
    1dc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1e0: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1e4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1e8: ffb4d2b7  lui          x5, 0xffb4d  # x5 = 0xffb4d000
    1ec: 02828293  addi         x5, x5, 40  # x5 = 0xffb4d028
    1f0: 0042a023  sw           x4, 0(x5)  # 0xffb4d028; write runtime value
    1f4: 0ff0000f  fence        0xf, 0xf
    1f8: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    1fc: 11428293  addi         x5, x5, 276  # x5 = 0x00008114
    200: 0002a203  lw           x4, 0(x5)  # param e2e_l0_gate_rows; 0x00008114
    204: 7c400393  addi         x7, x0, 1988  # x7 = 0x000007c4
    208: 0003a283  lw           x5, 0(x7)  # param e2e_l0_gate; 0x000007c4
    20c: ff82f293  andi         x5, x5, -8
    210: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    214: 10448493  addi         x9, x9, 260  # x9 = 0x00008104
    218: 0004a383  lw           x7, 0(x9)  # param e2e_l0_gate_row_start; 0x00008104
    21c: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    220: 028383b3  mul          x7, x7, x8
    224: 0073f313  andi         x6, x7, 7
    228: 0033d393  srli         x7, x7, 3
    22c: 00b39393  slli         x7, x7, 11
    230: 007282b3  add          x5, x5, x7
    234: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    238: 00020413  addi         x8, x4, 0
loc_23c:
    23c: 0e83f263  bgeu         x7, x8, 0x00000320  # target 0x00000320
    240: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    244: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    248: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_24c:
    24c: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    250: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    254: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    258: 40a485b3  sub          x11, x9, x10
    25c: 01059593  slli         x11, x11, 16
    260: 0105d593  srli         x11, x11, 16
    264: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    268: 40b60633  sub          x12, x12, x11
    26c: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    270: 00d67663  bgeu         x12, x13, 0x0000027c  # target 0x0000027c
    274: 0ff0000f  fence        0xf, 0xf
    278: fd5ff06f  jal          x0, 0x0000024c  # target 0x0000024c
loc_27c:
    27c: 0ff0000f  fence        0xf, 0xf
    280: 1cc000ef  jal          x1, 0x0000044c  # target 0x0000044c; x1 = 0x00000284
    284: 1e4000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000288
    288: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    28c: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    290: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    294: 00028f93  addi         x31, x5, 0
    298: 00030f13  addi         x30, x6, 0
    29c: 00048e93  addi         x29, x9, 0
    2a0: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    2a4: 38c000ef  jal          x1, 0x00000630  # target 0x00000630; x1 = 0x000002a8
    2a8: 000f8293  addi         x5, x31, 0
    2ac: 000f0313  addi         x6, x30, 0
    2b0: 1b8000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x000002b4
    2b4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2b8: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2bc: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    2c0: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    2c4: 00a484b3  add          x9, x9, x10
    2c8: 000945b7  lui          x11, 0x00094  # x11 = 0x00094000
    2cc: 00b4e663  bltu         x9, x11, 0x000002d8  # target 0x000002d8
    2d0: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    2d4: 40c484b3  sub          x9, x9, x12
loc_2d8:
    2d8: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2dc: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2e0: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    2e4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2e8: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    2ec: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    2f0: 00448493  addi         x9, x9, 4
    2f4: 01049493  slli         x9, x9, 16
    2f8: 0104d493  srli         x9, x9, 16
    2fc: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    300: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    304: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    308: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    30c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    310: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    314: 0ff0000f  fence        0xf, 0xf
    318: 00138393  addi         x7, x7, 1
    31c: f21ff06f  jal          x0, 0x0000023c  # target 0x0000023c
loc_320:
    320: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    324: 11828293  addi         x5, x5, 280  # x5 = 0x00008118
    328: 0002a203  lw           x4, 0(x5)  # param e2e_l0_up_rows; 0x00008118
    32c: 7c800393  addi         x7, x0, 1992  # x7 = 0x000007c8
    330: 0003a283  lw           x5, 0(x7)  # param e2e_l0_up; 0x000007c8
    334: ff82f293  andi         x5, x5, -8
    338: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    33c: 10c48493  addi         x9, x9, 268  # x9 = 0x0000810c
    340: 0004a383  lw           x7, 0(x9)  # param e2e_l0_up_row_start; 0x0000810c
    344: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    348: 028383b3  mul          x7, x7, x8
    34c: 0073f313  andi         x6, x7, 7
    350: 0033d393  srli         x7, x7, 3
    354: 00b39393  slli         x7, x7, 11
    358: 007282b3  add          x5, x5, x7
    35c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    360: 00020413  addi         x8, x4, 0
loc_364:
    364: 0e83f263  bgeu         x7, x8, 0x00000448  # target 0x00000448
    368: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    36c: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    370: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_374:
    374: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    378: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    37c: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    380: 40a485b3  sub          x11, x9, x10
    384: 01059593  slli         x11, x11, 16
    388: 0105d593  srli         x11, x11, 16
    38c: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    390: 40b60633  sub          x12, x12, x11
    394: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    398: 00d67663  bgeu         x12, x13, 0x000003a4  # target 0x000003a4
    39c: 0ff0000f  fence        0xf, 0xf
    3a0: fd5ff06f  jal          x0, 0x00000374  # target 0x00000374
loc_3a4:
    3a4: 0ff0000f  fence        0xf, 0xf
    3a8: 0a4000ef  jal          x1, 0x0000044c  # target 0x0000044c; x1 = 0x000003ac
    3ac: 0bc000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x000003b0
    3b0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3b4: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    3b8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    3bc: 00028f93  addi         x31, x5, 0
    3c0: 00030f13  addi         x30, x6, 0
    3c4: 00048e93  addi         x29, x9, 0
    3c8: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    3cc: 264000ef  jal          x1, 0x00000630  # target 0x00000630; x1 = 0x000003d0
    3d0: 000f8293  addi         x5, x31, 0
    3d4: 000f0313  addi         x6, x30, 0
    3d8: 090000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x000003dc
    3dc: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    3e0: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    3e4: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    3e8: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    3ec: 00a484b3  add          x9, x9, x10
    3f0: 000945b7  lui          x11, 0x00094  # x11 = 0x00094000
    3f4: 00b4e663  bltu         x9, x11, 0x00000400  # target 0x00000400
    3f8: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    3fc: 40c484b3  sub          x9, x9, x12
loc_400:
    400: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    404: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    408: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    40c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    410: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    414: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    418: 00448493  addi         x9, x9, 4
    41c: 01049493  slli         x9, x9, 16
    420: 0104d493  srli         x9, x9, 16
    424: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    428: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    42c: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    430: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    434: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    438: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    43c: 0ff0000f  fence        0xf, 0xf
    440: 00138393  addi         x7, x7, 1
    444: f21ff06f  jal          x0, 0x00000364  # target 0x00000364
loc_448:
    448: 3100006f  jal          x0, 0x00000758  # target 0x00000758
loc_44c:
    44c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    450: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    454: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    458: 000a0463  beq          x20, x0, 0x00000460  # target 0x00000460
    45c: ff1ff06f  jal          x0, 0x0000044c  # target 0x0000044c
loc_460:
    460: 0ff0000f  fence        0xf, 0xf
    464: 00008067  jalr         x0, 0(x1)
loc_468:
    468: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    46c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    470: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    474: 000a0463  beq          x20, x0, 0x0000047c  # target 0x0000047c
    478: ff1ff06f  jal          x0, 0x00000468  # target 0x00000468
loc_47c:
    47c: 0ff0000f  fence        0xf, 0xf
    480: 00008067  jalr         x0, 0(x1)
loc_484:
    484: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    488: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b_decode_token; 0x000007c0
    48c: 007a7d13  andi         x26, x20, 7
    490: ff8a7a13  andi         x20, x20, -8
    494: 01af8ab3  add          x21, x31, x26
    498: 007afb93  andi         x23, x21, 7
    49c: 003ada93  srli         x21, x21, 3
    4a0: 00ba9a93  slli         x21, x21, 11
    4a4: 014a8ab3  add          x21, x21, x20
    4a8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004a8
    4ac: 030b0b13  addi         x22, x22, 48  # x22 = 0x000004d8
    4b0: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    4b4: 11ce8e93  addi         x29, x29, 284  # x29 = 0x0000811c
    4b8: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000811c
    4bc: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    4c0: 03cd8db3  mul          x27, x27, x28
    4c4: 01bb0b33  add          x22, x22, x27
    4c8: 001b9b93  slli         x23, x23, 1
    4cc: 017b0b33  add          x22, x22, x23
    4d0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4d4: 00008067  jalr         x0, 0(x1)
    4d8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4dc: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4e0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4e4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    4e8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4ec: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f0: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    4f4: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    4f8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    4fc: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    500: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    504: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_508:
    508: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    50c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    510: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    514: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    518: 015a6463  bltu         x20, x21, 0x00000520  # target 0x00000520
    51c: fedff06f  jal          x0, 0x00000508  # target 0x00000508
loc_520:
    520: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    524: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    528: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    52c: 014a1a13  slli         x20, x20, 20
    530: 014a5a13  srli         x20, x20, 20
    534: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_538:
    538: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    53c: 000b0463  beq          x22, x0, 0x00000544  # target 0x00000544
    540: ff9ff06f  jal          x0, 0x00000538  # target 0x00000538
loc_544:
    544: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    548: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    54c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    550: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    554: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    558: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    55c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    560: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    564: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    568: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    56c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    570: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    574: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    578: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    57c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    580: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    584: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    588: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    58c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    590: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    594: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    598: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_59c:
    59c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5a0: 000b0463  beq          x22, x0, 0x000005a8  # target 0x000005a8
    5a4: ff9ff06f  jal          x0, 0x0000059c  # target 0x0000059c
loc_5a8:
    5a8: 00008067  jalr         x0, 0(x1)
loc_5ac:
    5ac: 7d000a93  addi         x21, x0, 2000  # x21 = 0x000007d0
    5b0: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_post_norm; 0x000007d0
    5b4: 007a7d13  andi         x26, x20, 7
    5b8: ff8a7a13  andi         x20, x20, -8
    5bc: 01af8ab3  add          x21, x31, x26
    5c0: 007afb93  andi         x23, x21, 7
    5c4: 003ada93  srli         x21, x21, 3
    5c8: 00ba9a93  slli         x21, x21, 11
    5cc: 014a8ab3  add          x21, x21, x20
    5d0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005d0
    5d4: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000600
    5d8: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    5dc: 11ce8e93  addi         x29, x29, 284  # x29 = 0x0000811c
    5e0: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000811c
    5e4: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    5e8: 03cd8db3  mul          x27, x27, x28
    5ec: 01bb0b33  add          x22, x22, x27
    5f0: 001b9b93  slli         x23, x23, 1
    5f4: 017b0b33  add          x22, x22, x23
    5f8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    5fc: 00008067  jalr         x0, 0(x1)
    600: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    604: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    608: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    60c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    610: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    614: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    618: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    61c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    620: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    624: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    628: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    62c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_630:
    630: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000630
    634: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x00000728
    638: 00008cb7  lui          x25, 0x00008  # x25 = 0x00008000
    63c: 11cc8c93  addi         x25, x25, 284  # x25 = 0x0000811c
    640: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0000811c
    644: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    648: 038b8bb3  mul          x23, x23, x24
    64c: 017a0a33  add          x20, x20, x23
loc_650:
    650: 001f1a93  slli         x21, x30, 1
    654: 014a8ab3  add          x21, x21, x20
    658: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_65c:
    65c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    660: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    664: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    668: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    66c: 018be463  bltu         x23, x24, 0x00000674  # target 0x00000674
    670: fedff06f  jal          x0, 0x0000065c  # target 0x0000065c
loc_674:
    674: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    678: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    67c: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    680: 014b9b93  slli         x23, x23, 20
    684: 014bdb93  srli         x23, x23, 20
    688: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_68c:
    68c: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    690: 000c8463  beq          x25, x0, 0x00000698  # target 0x00000698
    694: ff9ff06f  jal          x0, 0x0000068c  # target 0x0000068c
loc_698:
    698: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    69c: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    6a0: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    6a4: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    6a8: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    6ac: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    6b0: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    6b4: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    6b8: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    6bc: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    6c0: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    6c4: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    6c8: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6cc: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    6d0: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    6d4: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    6d8: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    6dc: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    6e0: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    6e4: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    6e8: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    6ec: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_6f0:
    6f0: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    6f4: 000c8463  beq          x25, x0, 0x000006fc  # target 0x000006fc
    6f8: ff9ff06f  jal          x0, 0x000006f0  # target 0x000006f0
loc_6fc:
    6fc: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    700: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    704: 016e8eb3  add          x29, x29, x22
    708: 001f0f13  addi         x30, x30, 1
    70c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    710: 015f1663  bne          x30, x21, 0x0000071c  # target 0x0000071c
    714: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    718: 016f8fb3  add          x31, x31, x22
loc_71c:
    71c: fffe0e13  addi         x28, x28, -1
    720: f20e18e3  bne          x28, x0, 0x00000650  # target 0x00000650
    724: 00008067  jalr         x0, 0(x1)
    728: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    72c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    730: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    734: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    738: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    73c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    740: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    744: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    748: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    74c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    750: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    754: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    758:           j FW_BRISC+4   # return to firmware, linked at install
