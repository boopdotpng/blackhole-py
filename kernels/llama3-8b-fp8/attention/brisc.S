# llama3 8b-fp8 decode: attention, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (32): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3
# params: 0x7c0=e2e_q_heads, 0x7c4=e2e_l0_key_cache, 0x7c8=e2e_l0_value_cache, 0x7cc=e2e_context, 0x7d0=kv_blocks, 0x7d4=valid_columns, 0x7d8=attention_e2e_q_compact, 0x7dc=attention_e2e_k_compact, 0x7e0=attention_e2e_v_compact, 0x7e4=e2e_rope_cos, 0x7e8=e2e_rope_sin, 0x7ec=start_pos, 0x80c0=attention_core
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000a02b7  lui          x5, 0x000a0  # x5 = 0x000a0000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x000a0000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     20: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     24: 000a32b7  lui          x5, 0x000a3  # x5 = 0x000a3000
     28: 80028293  addi         x5, x5, -2048  # x5 = 0x000a2800
     2c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x000a2800
     30: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     34: 88420213  addi         x4, x4, -1916  # x4 = 0xffb00884 · riscv_local_mem + 0x884
     38: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     3c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     40: 88838393  addi         x7, x7, -1912  # x7 = 0xffb00888 · riscv_local_mem + 0x888
     44: 0009d437  lui          x8, 0x0009d  # x8 = 0x0009d000
     48: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x888 · 0xffb00888; write 0x0009d000
     4c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     50: 88c38393  addi         x7, x7, -1908  # x7 = 0xffb0088c · riscv_local_mem + 0x88c
     54: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x88c · 0xffb0088c; write 0x00000000
     58: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     5c: 89038393  addi         x7, x7, -1904  # x7 = 0xffb00890 · riscv_local_mem + 0x890
     60: 0009c437  lui          x8, 0x0009c  # x8 = 0x0009c000
     64: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x890 · 0xffb00890; write 0x0009c000
     68: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     6c: 89438393  addi         x7, x7, -1900  # x7 = 0xffb00894 · riscv_local_mem + 0x894
     70: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x894 · 0xffb00894; write 0x00000000
     74: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     78: 89848493  addi         x9, x9, -1896  # x9 = 0xffb00898 · riscv_local_mem + 0x898
     7c: 00090537  lui          x10, 0x00090  # x10 = 0x00090000
     80: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x898 · 0xffb00898; write 0x00090000
     84: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     88: 89c48493  addi         x9, x9, -1892  # x9 = 0xffb0089c · riscv_local_mem + 0x89c
     8c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x89c · 0xffb0089c; write 0x00000000
     90: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     94: 8a058593  addi         x11, x11, -1888  # x11 = 0xffb008a0 · riscv_local_mem + 0x8a0
     98: 00092637  lui          x12, 0x00092  # x12 = 0x00092000
     9c: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x8a0 · 0xffb008a0; write 0x00092000
     a0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     a4: 8a458593  addi         x11, x11, -1884  # x11 = 0xffb008a4 · riscv_local_mem + 0x8a4
     a8: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x8a4 · 0xffb008a4; write 0x00000000
     ac: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     b0: 8a858593  addi         x11, x11, -1880  # x11 = 0xffb008a8 · riscv_local_mem + 0x8a8
     b4: 00096637  lui          x12, 0x00096  # x12 = 0x00096000
     b8: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x8a8 · 0xffb008a8; write 0x00096000
     bc: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     c0: 8ac58593  addi         x11, x11, -1876  # x11 = 0xffb008ac · riscv_local_mem + 0x8ac
     c4: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x8ac · 0xffb008ac; write 0x00000000
     c8: 7ec00393  addi         x7, x0, 2028  # x7 = 0x000007ec
     cc: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ec
     d0: 00325293  srli         x5, x4, 3
     d4: 00727313  andi         x6, x4, 7
     d8: 00731313  slli         x6, x6, 7
     dc: 00131313  slli         x6, x6, 1
     e0: 389000ef  jal          x1, 0x00000c68  # target 0x00000c68; x1 = 0x000000e4
     e4: 3a1000ef  jal          x1, 0x00000c84  # target 0x00000c84; x1 = 0x000000e8
     e8: 00028f93  addi         x31, x5, 0
     ec: 3b5000ef  jal          x1, 0x00000ca0  # target 0x00000ca0; x1 = 0x000000f0
     f0: 000a8393  addi         x7, x21, 0
     f4: 000b0413  addi         x8, x22, 0
     f8: 00038f93  addi         x31, x7, 0
     fc: 00040f13  addi         x30, x8, 0
    100: 000b8eb7  lui          x29, 0x000b8  # x29 = 0x000b8000
    104: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000b7800
    108: 3e5000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x0000010c
    10c: 00028f93  addi         x31, x5, 0
    110: 481000ef  jal          x1, 0x00000d90  # target 0x00000d90; x1 = 0x00000114
    114: 000a8393  addi         x7, x21, 0
    118: 000b0413  addi         x8, x22, 0
    11c: 00038f93  addi         x31, x7, 0
    120: 00040f13  addi         x30, x8, 0
    124: 000b8eb7  lui          x29, 0x000b8  # x29 = 0x000b8000
    128: 3c5000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x0000012c
    12c: 359000ef  jal          x1, 0x00000c84  # target 0x00000c84; x1 = 0x00000130
    130: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    134: 0c048493  addi         x9, x9, 192  # x9 = 0x000080c0
    138: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x000080c0
    13c: 00741413  slli         x8, x8, 7
    140: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
loc_144:
    144: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    148: ac068693  addi         x13, x13, -1344  # x13 = 0x00000ac0
    14c: 00d47c63  bgeu         x8, x13, 0x00000164  # target 0x00000164
    150: 02b00613  addi         x12, x0, 43  # x12 = 0x0000002b
    154: 02c454b3  divu         x9, x8, x12
    158: 02c485b3  mul          x11, x9, x12
    15c: 40b405b3  sub          x11, x8, x11
    160: 01c0006f  jal          x0, 0x0000017c  # target 0x0000017c
loc_164:
    164: 40d406b3  sub          x13, x8, x13
    168: 02a00613  addi         x12, x0, 42  # x12 = 0x0000002a
    16c: 02c6d4b3  divu         x9, x13, x12
    170: 02c485b3  mul          x11, x9, x12
    174: 40b685b3  sub          x11, x13, x11
    178: 04048493  addi         x9, x9, 64
loc_17c:
    17c: 07f40513  addi         x10, x8, 127
    180: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    184: ac078793  addi         x15, x15, -1344  # x15 = 0x00000ac0
    188: 00f57c63  bgeu         x10, x15, 0x000001a0  # target 0x000001a0
    18c: 02b00713  addi         x14, x0, 43  # x14 = 0x0000002b
    190: 02e55633  divu         x12, x10, x14
    194: 02e606b3  mul          x13, x12, x14
    198: 40d506b3  sub          x13, x10, x13
    19c: 01c0006f  jal          x0, 0x000001b8  # target 0x000001b8
loc_1a0:
    1a0: 40f507b3  sub          x15, x10, x15
    1a4: 02a00713  addi         x14, x0, 42  # x14 = 0x0000002a
    1a8: 02e7d633  divu         x12, x15, x14
    1ac: 02e606b3  mul          x13, x12, x14
    1b0: 40d786b3  sub          x13, x15, x13
    1b4: 04060613  addi         x12, x12, 64
loc_1b8:
    1b8: 00048513  addi         x10, x9, 0
    1bc: 2ad000ef  jal          x1, 0x00000c68  # target 0x00000c68; x1 = 0x000001c0
    1c0: 2c5000ef  jal          x1, 0x00000c84  # target 0x00000c84; x1 = 0x000001c4
    1c4: 000a3737  lui          x14, 0x000a3  # x14 = 0x000a3000
loc_1c8:
    1c8: 00050f93  addi         x31, x10, 0
    1cc: 411000ef  jal          x1, 0x00000ddc  # target 0x00000ddc; x1 = 0x000001d0
    1d0: 000a8793  addi         x15, x21, 0
    1d4: 000b0813  addi         x16, x22, 0
    1d8: 00078f93  addi         x31, x15, 0
    1dc: 00080f13  addi         x30, x16, 0
    1e0: 00070e93  addi         x29, x14, 0
    1e4: 309000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x000001e8
    1e8: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1ec: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    1f0: 00f70733  add          x14, x14, x15
    1f4: 00150513  addi         x10, x10, 1
    1f8: fca678e3  bgeu         x12, x10, 0x000001c8  # target 0x000001c8
    1fc: 289000ef  jal          x1, 0x00000c84  # target 0x00000c84; x1 = 0x00000200
    200: 00048513  addi         x10, x9, 0
    204: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    208: 00839693  slli         x13, x7, 8
    20c: 000a0737  lui          x14, 0x000a0  # x14 = 0x000a0000
    210: 00e686b3  add          x13, x13, x14
loc_214:
    214: 02a00713  addi         x14, x0, 42  # x14 = 0x0000002a
    218: 04000793  addi         x15, x0, 64  # x15 = 0x00000040
    21c: 00f57463  bgeu         x10, x15, 0x00000224  # target 0x00000224
    220: 00170713  addi         x14, x14, 1  # x14 = 0x0000002b
loc_224:
    224: 40b70733  sub          x14, x14, x11
    228: 00f5f793  andi         x15, x11, 15
    22c: 40f007b3  sub          x15, x0, x15
    230: 01078793  addi         x15, x15, 16
    234: 00e7f463  bgeu         x15, x14, 0x0000023c  # target 0x0000023c
    238: 00078713  addi         x14, x15, 0
loc_23c:
    23c: 03f67793  andi         x15, x12, 63
    240: 40f007b3  sub          x15, x0, x15
    244: 04078793  addi         x15, x15, 64
    248: 00e7f463  bgeu         x15, x14, 0x00000250  # target 0x00000250
    24c: 00078713  addi         x14, x15, 0
loc_250:
    250: 40950833  sub          x16, x10, x9
    254: 00b81813  slli         x16, x16, 11
    258: 00f5f793  andi         x15, x11, 15
    25c: 00179793  slli         x15, x15, 1
    260: 0105fa13  andi         x20, x11, 16
    264: 005a1a13  slli         x20, x20, 5
    268: 0147e7b3  or           x15, x15, x20
    26c: 1e05fa13  andi         x20, x11, 480
    270: 0147e7b3  or           x15, x15, x20
    274: 0095da13  srli         x20, x11, 9
    278: 00aa1a13  slli         x20, x20, 10
    27c: 0147e7b3  or           x15, x15, x20
    280: 00f80833  add          x16, x16, x15
    284: 000a3a37  lui          x20, 0x000a3  # x20 = 0x000a3000
    288: 01480833  add          x16, x16, x20
    28c: 00161893  slli         x17, x12, 1
    290: 00d888b3  add          x17, x17, x13
    294: 04064913  xori         x18, x12, 64
    298: 00191913  slli         x18, x18, 1
    29c: 00d90933  add          x18, x18, x13
    2a0: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2a4: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    2a8: 01490933  add          x18, x18, x20
    2ac: 04067993  andi         x19, x12, 64
    2b0: 00999993  slli         x19, x19, 9
    2b4: 00080f93  addi         x31, x16, 0
    2b8: 00088f13  addi         x30, x17, 0
    2bc: 00090e93  addi         x29, x18, 0
    2c0: 00070e13  addi         x28, x14, 0
    2c4: 00098d93  addi         x27, x19, 0
loc_2c8:
    2c8: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    2cc: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    2d0: 01ba4a33  xor          x20, x20, x27
    2d4: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    2d8: 002f8f93  addi         x31, x31, 2
    2dc: 002f0f13  addi         x30, x30, 2
    2e0: 002e8e93  addi         x29, x29, 2
    2e4: fffe0e13  addi         x28, x28, -1
    2e8: fe0e10e3  bne          x28, x0, 0x000002c8  # target 0x000002c8
    2ec: 00e60633  add          x12, x12, x14
    2f0: 00e585b3  add          x11, x11, x14
    2f4: 02a00793  addi         x15, x0, 42  # x15 = 0x0000002a
    2f8: 04000993  addi         x19, x0, 64  # x19 = 0x00000040
    2fc: 01357463  bgeu         x10, x19, 0x00000304  # target 0x00000304
    300: 00178793  addi         x15, x15, 1  # x15 = 0x0000002b
loc_304:
    304: 00f59663  bne          x11, x15, 0x00000310  # target 0x00000310
    308: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    30c: 00150513  addi         x10, x10, 1
loc_310:
    310: 08000793  addi         x15, x0, 128  # x15 = 0x00000080
    314: f0f660e3  bltu         x12, x15, 0x00000214  # target 0x00000214
    318: 08040413  addi         x8, x8, 128
    31c: 00138393  addi         x7, x7, 1
    320: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
    324: e29390e3  bne          x7, x9, 0x00000144  # target 0x00000144
    328: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    32c: 0c048493  addi         x9, x9, 192  # x9 = 0x000080c0
    330: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x000080c0
    334: 00245413  srli         x8, x8, 2
    338: 00741413  slli         x8, x8, 7
    33c: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
    340: 2c000693  addi         x13, x0, 704  # x13 = 0x000002c0
    344: 00d47c63  bgeu         x8, x13, 0x0000035c  # target 0x0000035c
    348: 00b00613  addi         x12, x0, 11  # x12 = 0x0000000b
    34c: 02c454b3  divu         x9, x8, x12
    350: 02c485b3  mul          x11, x9, x12
    354: 40b405b3  sub          x11, x8, x11
    358: 01c0006f  jal          x0, 0x00000374  # target 0x00000374
loc_35c:
    35c: 40d406b3  sub          x13, x8, x13
    360: 00a00613  addi         x12, x0, 10  # x12 = 0x0000000a
    364: 02c6d4b3  divu         x9, x13, x12
    368: 02c485b3  mul          x11, x9, x12
    36c: 40b685b3  sub          x11, x13, x11
    370: 04048493  addi         x9, x9, 64
loc_374:
    374: 07f40513  addi         x10, x8, 127
    378: 2c000793  addi         x15, x0, 704  # x15 = 0x000002c0
    37c: 00f57c63  bgeu         x10, x15, 0x00000394  # target 0x00000394
    380: 00b00713  addi         x14, x0, 11  # x14 = 0x0000000b
    384: 02e55633  divu         x12, x10, x14
    388: 02e606b3  mul          x13, x12, x14
    38c: 40d506b3  sub          x13, x10, x13
    390: 01c0006f  jal          x0, 0x000003ac  # target 0x000003ac
loc_394:
    394: 40f507b3  sub          x15, x10, x15
    398: 00a00713  addi         x14, x0, 10  # x14 = 0x0000000a
    39c: 02e7d633  divu         x12, x15, x14
    3a0: 02e606b3  mul          x13, x12, x14
    3a4: 40d786b3  sub          x13, x15, x13
    3a8: 04060613  addi         x12, x12, 64
loc_3ac:
    3ac: 00048513  addi         x10, x9, 0
    3b0: 0b9000ef  jal          x1, 0x00000c68  # target 0x00000c68; x1 = 0x000003b4
    3b4: 0d1000ef  jal          x1, 0x00000c84  # target 0x00000c84; x1 = 0x000003b8
    3b8: 000a3737  lui          x14, 0x000a3  # x14 = 0x000a3000
loc_3bc:
    3bc: 00050f93  addi         x31, x10, 0
    3c0: 269000ef  jal          x1, 0x00000e28  # target 0x00000e28; x1 = 0x000003c4
    3c4: 000a8793  addi         x15, x21, 0
    3c8: 000b0813  addi         x16, x22, 0
    3cc: 00078f93  addi         x31, x15, 0
    3d0: 00080f13  addi         x30, x16, 0
    3d4: 00070e93  addi         x29, x14, 0
    3d8: 115000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x000003dc
    3dc: 00050f93  addi         x31, x10, 0
    3e0: 295000ef  jal          x1, 0x00000e74  # target 0x00000e74; x1 = 0x000003e4
    3e4: 000a8793  addi         x15, x21, 0
    3e8: 000b0813  addi         x16, x22, 0
    3ec: 0000a8b7  lui          x17, 0x0000a  # x17 = 0x0000a000
    3f0: 00e888b3  add          x17, x17, x14
    3f4: 00078f93  addi         x31, x15, 0
    3f8: 00080f13  addi         x30, x16, 0
    3fc: 00088e93  addi         x29, x17, 0
    400: 0ed000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x00000404
    404: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    408: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    40c: 00f70733  add          x14, x14, x15
    410: 00150513  addi         x10, x10, 1
    414: faa674e3  bgeu         x12, x10, 0x000003bc  # target 0x000003bc
    418: 06d000ef  jal          x1, 0x00000c84  # target 0x00000c84; x1 = 0x0000041c
    41c: 00048513  addi         x10, x9, 0
    420: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    424: 00839693  slli         x13, x7, 8
    428: 000a0737  lui          x14, 0x000a0  # x14 = 0x000a0000
    42c: 00e686b3  add          x13, x13, x14
loc_430:
    430: 00a00713  addi         x14, x0, 10  # x14 = 0x0000000a
    434: 04000793  addi         x15, x0, 64  # x15 = 0x00000040
    438: 00f57463  bgeu         x10, x15, 0x00000440  # target 0x00000440
    43c: 00170713  addi         x14, x14, 1  # x14 = 0x0000000b
loc_440:
    440: 40b70733  sub          x14, x14, x11
    444: 00f5f793  andi         x15, x11, 15
    448: 40f007b3  sub          x15, x0, x15
    44c: 01078793  addi         x15, x15, 16
    450: 00e7f463  bgeu         x15, x14, 0x00000458  # target 0x00000458
    454: 00078713  addi         x14, x15, 0
loc_458:
    458: 03f67793  andi         x15, x12, 63
    45c: 40f007b3  sub          x15, x0, x15
    460: 04078793  addi         x15, x15, 64
    464: 00e7f463  bgeu         x15, x14, 0x0000046c  # target 0x0000046c
    468: 00078713  addi         x14, x15, 0
loc_46c:
    46c: 40950833  sub          x16, x10, x9
    470: 00b81813  slli         x16, x16, 11
    474: 00f5f793  andi         x15, x11, 15
    478: 00179793  slli         x15, x15, 1
    47c: 0105fa13  andi         x20, x11, 16
    480: 005a1a13  slli         x20, x20, 5
    484: 0147e7b3  or           x15, x15, x20
    488: 1e05fa13  andi         x20, x11, 480
    48c: 0147e7b3  or           x15, x15, x20
    490: 0095da13  srli         x20, x11, 9
    494: 00aa1a13  slli         x20, x20, 10
    498: 0147e7b3  or           x15, x15, x20
    49c: 00f80833  add          x16, x16, x15
    4a0: 000a3a37  lui          x20, 0x000a3  # x20 = 0x000a3000
    4a4: 01480833  add          x16, x16, x20
    4a8: 00161893  slli         x17, x12, 1
    4ac: 00d888b3  add          x17, x17, x13
    4b0: 04064913  xori         x18, x12, 64
    4b4: 00191913  slli         x18, x18, 1
    4b8: 00d90933  add          x18, x18, x13
    4bc: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4c0: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    4c4: 01490933  add          x18, x18, x20
    4c8: 04067993  andi         x19, x12, 64
    4cc: 00999993  slli         x19, x19, 9
    4d0: 0000aa37  lui          x20, 0x0000a  # x20 = 0x0000a000
    4d4: 010a0a33  add          x20, x20, x16
    4d8: 00161a93  slli         x21, x12, 1
    4dc: 000b7b37  lui          x22, 0x000b7  # x22 = 0x000b7000
    4e0: 016a8ab3  add          x21, x21, x22
    4e4: ffc10113  addi         x2, x2, -4
    4e8: 01412023  sw           x20, 0(x2)  # Address depends on runtime register values
    4ec: 00080f93  addi         x31, x16, 0
    4f0: 00088f13  addi         x30, x17, 0
    4f4: 00090e93  addi         x29, x18, 0
    4f8: 00070e13  addi         x28, x14, 0
    4fc: 00098d93  addi         x27, x19, 0
    500: 000a0d13  addi         x26, x20, 0
    504: 000a8c93  addi         x25, x21, 0
loc_508:
    508: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    50c: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    510: 01ba4a33  xor          x20, x20, x27
    514: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    518: 000d5a03  lhu          x20, 0(x26)  # Address depends on runtime register values
    51c: 014c9023  sh           x20, 0(x25)  # Address depends on runtime register values
    520: 002d0d13  addi         x26, x26, 2
    524: 002c8c93  addi         x25, x25, 2
    528: 002f8f93  addi         x31, x31, 2
    52c: 002f0f13  addi         x30, x30, 2
    530: 002e8e93  addi         x29, x29, 2
    534: fffe0e13  addi         x28, x28, -1
    538: fc0e18e3  bne          x28, x0, 0x00000508  # target 0x00000508
    53c: 00012a03  lw           x20, 0(x2)  # Address depends on runtime register values
    540: 00410113  addi         x2, x2, 4
    544: 00e60633  add          x12, x12, x14
    548: 00e585b3  add          x11, x11, x14
    54c: 00a00793  addi         x15, x0, 10  # x15 = 0x0000000a
    550: 04000993  addi         x19, x0, 64  # x19 = 0x00000040
    554: 01357463  bgeu         x10, x19, 0x0000055c  # target 0x0000055c
    558: 00178793  addi         x15, x15, 1  # x15 = 0x0000000b
loc_55c:
    55c: 00f59663  bne          x11, x15, 0x00000568  # target 0x00000568
    560: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    564: 00150513  addi         x10, x10, 1
loc_568:
    568: 08000793  addi         x15, x0, 128  # x15 = 0x00000080
    56c: ecf662e3  bltu         x12, x15, 0x00000430  # target 0x00000430
    570: 000b83b7  lui          x7, 0x000b8  # x7 = 0x000b8000
    574: 80038393  addi         x7, x7, -2048  # x7 = 0x000b7800
    578: 006383b3  add          x7, x7, x6
    57c: 00038f93  addi         x31, x7, 0
    580: 000a1f37  lui          x30, 0x000a1  # x30 = 0x000a1000
    584: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    588: 139000ef  jal          x1, 0x00000ec0  # target 0x00000ec0; x1 = 0x0000058c
    58c: 000a1fb7  lui          x31, 0x000a1  # x31 = 0x000a1000
    590: 000a1f37  lui          x30, 0x000a1  # x30 = 0x000a1000
    594: 100f0f13  addi         x30, x30, 256  # x30 = 0x000a1100
    598: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    59c: 179000ef  jal          x1, 0x00000f14  # target 0x00000f14; x1 = 0x000005a0
    5a0: 000b83b7  lui          x7, 0x000b8  # x7 = 0x000b8000
    5a4: 006383b3  add          x7, x7, x6
    5a8: 00038f93  addi         x31, x7, 0
    5ac: 000a2f37  lui          x30, 0x000a2  # x30 = 0x000a2000
    5b0: 800f0f13  addi         x30, x30, -2048  # x30 = 0x000a1800
    5b4: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5b8: 109000ef  jal          x1, 0x00000ec0  # target 0x00000ec0; x1 = 0x000005bc
    5bc: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    5c0: 800f8f93  addi         x31, x31, -2048  # x31 = 0x000a1800
    5c4: 000a2f37  lui          x30, 0x000a2  # x30 = 0x000a2000
    5c8: 900f0f13  addi         x30, x30, -1792  # x30 = 0x000a1900
    5cc: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5d0: 145000ef  jal          x1, 0x00000f14  # target 0x00000f14; x1 = 0x000005d4
    5d4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    5d8: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    5dc: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    5e0: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    5e4: 00520233  add          x4, x4, x5
    5e8: 000a2337  lui          x6, 0x000a2  # x6 = 0x000a2000
    5ec: 00626663  bltu         x4, x6, 0x000005f8  # target 0x000005f8
    5f0: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    5f4: 40720233  sub          x4, x4, x7
loc_5f8:
    5f8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    5fc: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    600: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    604: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    608: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    60c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    610: 00420213  addi         x4, x4, 4
    614: 01021213  slli         x4, x4, 16
    618: 01025213  srli         x4, x4, 16
    61c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    620: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    624: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    628: ffb4f2b7  lui          x5, 0xffb4f  # x5 = 0xffb4f000
    62c: 02828293  addi         x5, x5, 40  # x5 = 0xffb4f028
    630: 0042a023  sw           x4, 0(x5)  # 0xffb4f028; write runtime value
    634: 0ff0000f  fence        0xf, 0xf
    638: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    63c: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
    640: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884
    644: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_648:
    648: ffb51437  lui          x8, 0xffb51  # x8 = 0xffb51000
    64c: 02840413  addi         x8, x8, 40  # x8 = 0xffb51028
    650: 00045283  lhu          x5, 0(x8)  # 0xffb51028
    654: 40428333  sub          x6, x5, x4
    658: 01031313  slli         x6, x6, 16
    65c: 01035313  srli         x6, x6, 16
    660: 00737663  bgeu         x6, x7, 0x0000066c  # target 0x0000066c
    664: 0ff0000f  fence        0xf, 0xf
    668: fe1ff06f  jal          x0, 0x00000648  # target 0x00000648
loc_66c:
    66c: 0ff0000f  fence        0xf, 0xf
    670: 000083b7  lui          x7, 0x00008  # x7 = 0x00008000
    674: 0c038393  addi         x7, x7, 192  # x7 = 0x000080c0
    678: 0003a203  lw           x4, 0(x7)  # param attention_core; 0x000080c0
    67c: 7d000393  addi         x7, x0, 2000  # x7 = 0x000007d0
    680: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x000007d0
    684: 7d400393  addi         x7, x0, 2004  # x7 = 0x000007d4
    688: 0003a303  lw           x6, 0(x7)  # param valid_columns; 0x000007d4
    68c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    690: 88c60613  addi         x12, x12, -1908  # x12 = 0xffb0088c · riscv_local_mem + 0x88c
    694: 00062383  lw           x7, 0(x12)  # riscv_local_mem + 0x88c · 0xffb0088c
loc_698:
    698: ffb4d637  lui          x12, 0xffb4d  # x12 = 0xffb4d000
    69c: 02060613  addi         x12, x12, 32  # x12 = 0xffb4d020
    6a0: 00065403  lhu          x8, 0(x12)  # 0xffb4d020
    6a4: 408384b3  sub          x9, x7, x8
    6a8: 01049493  slli         x9, x9, 16
    6ac: 0104d493  srli         x9, x9, 16
    6b0: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
    6b4: 40950533  sub          x10, x10, x9
    6b8: 00100593  addi         x11, x0, 1  # x11 = 0x00000001
    6bc: 00b57663  bgeu         x10, x11, 0x000006c8  # target 0x000006c8
    6c0: 0ff0000f  fence        0xf, 0xf
    6c4: fd5ff06f  jal          x0, 0x00000698  # target 0x00000698
loc_6c8:
    6c8: 0ff0000f  fence        0xf, 0xf
    6cc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6d0: 88840413  addi         x8, x8, -1912  # x8 = 0xffb00888 · riscv_local_mem + 0x888
    6d4: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x888 · 0xffb00888
    6d8: 00038413  addi         x8, x7, 0
    6dc: 40000493  addi         x9, x0, 1024  # x9 = 0x00000400
loc_6e0:
    6e0: 00042023  sw           x0, 0(x8)  # Address depends on runtime register values
    6e4: 00042223  sw           x0, 4(x8)  # Address depends on runtime register values
    6e8: 00042423  sw           x0, 8(x8)  # Address depends on runtime register values
    6ec: 00042623  sw           x0, 12(x8)  # Address depends on runtime register values
    6f0: 00042823  sw           x0, 16(x8)  # Address depends on runtime register values
    6f4: 00042a23  sw           x0, 20(x8)  # Address depends on runtime register values
    6f8: 00042c23  sw           x0, 24(x8)  # Address depends on runtime register values
    6fc: 00042e23  sw           x0, 28(x8)  # Address depends on runtime register values
    700: 02040413  addi         x8, x8, 32
    704: ff848493  addi         x9, x9, -8
    708: fc049ce3  bne          x9, x0, 0x000006e0  # target 0x000006e0
    70c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    710: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    714: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888
    718: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    71c: 008383b3  add          x7, x7, x8
    720: 0009e4b7  lui          x9, 0x0009e  # x9 = 0x0009e000
    724: 0093e663  bltu         x7, x9, 0x00000730  # target 0x00000730
    728: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    72c: 40a383b3  sub          x7, x7, x10
loc_730:
    730: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    734: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    738: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
    73c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    740: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    744: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c
    748: 00138393  addi         x7, x7, 1
    74c: 01039393  slli         x7, x7, 16
    750: 0103d393  srli         x7, x7, 16
    754: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    758: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    75c: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c; write runtime value
    760: ffb4d437  lui          x8, 0xffb4d  # x8 = 0xffb4d000
    764: 02840413  addi         x8, x8, 40  # x8 = 0xffb4d028
    768: 00742023  sw           x7, 0(x8)  # 0xffb4d028; write runtime value
    76c: 0ff0000f  fence        0xf, 0xf
    770: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    774: 89460613  addi         x12, x12, -1900  # x12 = 0xffb00894 · riscv_local_mem + 0x894
    778: 00062383  lw           x7, 0(x12)  # riscv_local_mem + 0x894 · 0xffb00894
loc_77c:
    77c: ffb4c637  lui          x12, 0xffb4c  # x12 = 0xffb4c000
    780: 02060613  addi         x12, x12, 32  # x12 = 0xffb4c020
    784: 00065403  lhu          x8, 0(x12)  # 0xffb4c020
    788: 408384b3  sub          x9, x7, x8
    78c: 01049493  slli         x9, x9, 16
    790: 0104d493  srli         x9, x9, 16
    794: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
    798: 40950533  sub          x10, x10, x9
    79c: 00100593  addi         x11, x0, 1  # x11 = 0x00000001
    7a0: 00b57663  bgeu         x10, x11, 0x000007ac  # target 0x000007ac
    7a4: 0ff0000f  fence        0xf, 0xf
    7a8: fd5ff06f  jal          x0, 0x0000077c  # target 0x0000077c
loc_7ac:
    7ac: 0ff0000f  fence        0xf, 0xf
    7b0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7b4: 89040413  addi         x8, x8, -1904  # x8 = 0xffb00890 · riscv_local_mem + 0x890
    7b8: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x890 · 0xffb00890
    7bc: 00038413  addi         x8, x7, 0
    7c0: 40000493  addi         x9, x0, 1024  # x9 = 0x00000400
loc_7c4:
    7c4: 00042023  sw           x0, 0(x8)  # Address depends on runtime register values
    7c8: 00042223  sw           x0, 4(x8)  # Address depends on runtime register values
    7cc: 00042423  sw           x0, 8(x8)  # Address depends on runtime register values
    7d0: 00042623  sw           x0, 12(x8)  # Address depends on runtime register values
    7d4: 00042823  sw           x0, 16(x8)  # Address depends on runtime register values
    7d8: 00042a23  sw           x0, 20(x8)  # Address depends on runtime register values
    7dc: 00042c23  sw           x0, 24(x8)  # Address depends on runtime register values
    7e0: 00042e23  sw           x0, 28(x8)  # Address depends on runtime register values
    7e4: 02040413  addi         x8, x8, 32
    7e8: ff848493  addi         x9, x9, -8
    7ec: fc049ce3  bne          x9, x0, 0x000007c4  # target 0x000007c4
    7f0: 00030413  addi         x8, x6, 0
    7f4: 02000493  addi         x9, x0, 32  # x9 = 0x00000020
    7f8: ff800537  lui          x10, 0xff800  # x10 = 0xff800000
loc_7fc:
    7fc: 02947463  bgeu         x8, x9, 0x00000824  # target 0x00000824
    800: 00445593  srli         x11, x8, 4
    804: 00a59593  slli         x11, x11, 10
    808: 00f47613  andi         x12, x8, 15
    80c: 00261613  slli         x12, x12, 2
    810: 00c586b3  add          x13, x11, x12
    814: 00d38733  add          x14, x7, x13
    818: 00a72023  sw           x10, 0(x14)  # Address depends on runtime register values
    81c: 00140413  addi         x8, x8, 1
    820: fddff06f  jal          x0, 0x000007fc  # target 0x000007fc
loc_824:
    824: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    828: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
    82c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890
    830: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    834: 008383b3  add          x7, x7, x8
    838: 0009d4b7  lui          x9, 0x0009d  # x9 = 0x0009d000
    83c: 0093e663  bltu         x7, x9, 0x00000848  # target 0x00000848
    840: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    844: 40a383b3  sub          x7, x7, x10
loc_848:
    848: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    84c: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
    850: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890; write runtime value
    854: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    858: 89440413  addi         x8, x8, -1900  # x8 = 0xffb00894 · riscv_local_mem + 0x894
    85c: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x894 · 0xffb00894
    860: 00138393  addi         x7, x7, 1
    864: 01039393  slli         x7, x7, 16
    868: 0103d393  srli         x7, x7, 16
    86c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    870: 89440413  addi         x8, x8, -1900  # x8 = 0xffb00894 · riscv_local_mem + 0x894
    874: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x894 · 0xffb00894; write runtime value
    878: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    87c: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    880: 00742023  sw           x7, 0(x8)  # 0xffb4c028; write runtime value
    884: 0ff0000f  fence        0xf, 0xf
    888: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    88c: 00028413  addi         x8, x5, 0
loc_890:
    890: 3c83fa63  bgeu         x7, x8, 0x00000c64  # target 0x00000c64
    894: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    898: 89c70713  addi         x14, x14, -1892  # x14 = 0xffb0089c · riscv_local_mem + 0x89c
    89c: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x89c · 0xffb0089c
loc_8a0:
    8a0: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    8a4: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    8a8: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    8ac: 40a485b3  sub          x11, x9, x10
    8b0: 01059593  slli         x11, x11, 16
    8b4: 0105d593  srli         x11, x11, 16
    8b8: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    8bc: 40b60633  sub          x12, x12, x11
    8c0: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    8c4: 00d67663  bgeu         x12, x13, 0x000008d0  # target 0x000008d0
    8c8: 0ff0000f  fence        0xf, 0xf
    8cc: fd5ff06f  jal          x0, 0x000008a0  # target 0x000008a0
loc_8d0:
    8d0: 0ff0000f  fence        0xf, 0xf
    8d4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    8d8: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    8dc: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898
    8e0: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    8e4: 00a484b3  add          x9, x9, x10
    8e8: 000925b7  lui          x11, 0x00092  # x11 = 0x00092000
    8ec: 00b4e663  bltu         x9, x11, 0x000008f8  # target 0x000008f8
    8f0: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    8f4: 40c484b3  sub          x9, x9, x12
loc_8f8:
    8f8: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    8fc: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    900: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898; write runtime value
    904: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    908: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    90c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c
    910: 00448493  addi         x9, x9, 4
    914: 01049493  slli         x9, x9, 16
    918: 0104d493  srli         x9, x9, 16
    91c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    920: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    924: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c; write runtime value
    928: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    92c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    930: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    934: 0ff0000f  fence        0xf, 0xf
    938: 00225493  srli         x9, x4, 2
    93c: 00a49493  slli         x9, x9, 10
    940: 00239513  slli         x10, x7, 2
    944: 00a484b3  add          x9, x9, x10
    948: 320000ef  jal          x1, 0x00000c68  # target 0x00000c68; x1 = 0x0000094c
    94c: 338000ef  jal          x1, 0x00000c84  # target 0x00000c84; x1 = 0x00000950
    950: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    954: 8a480813  addi         x16, x16, -1884  # x16 = 0xffb008a4 · riscv_local_mem + 0x8a4
    958: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x8a4 · 0xffb008a4
loc_95c:
    95c: ffb49837  lui          x16, 0xffb49  # x16 = 0xffb49000
    960: 02080813  addi         x16, x16, 32  # x16 = 0xffb49020
    964: 00085603  lhu          x12, 0(x16)  # 0xffb49020
    968: 40c586b3  sub          x13, x11, x12
    96c: 01069693  slli         x13, x13, 16
    970: 0106d693  srli         x13, x13, 16
    974: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    978: 40d70733  sub          x14, x14, x13
    97c: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    980: 00f77663  bgeu         x14, x15, 0x0000098c  # target 0x0000098c
    984: 0ff0000f  fence        0xf, 0xf
    988: fd5ff06f  jal          x0, 0x0000095c  # target 0x0000095c
loc_98c:
    98c: 0ff0000f  fence        0xf, 0xf
    990: 00048593  addi         x11, x9, 0
    994: 00058f93  addi         x31, x11, 0
    998: 598000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x0000099c
    99c: 000a8613  addi         x12, x21, 0
    9a0: 000b0693  addi         x13, x22, 0
    9a4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    9a8: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    9ac: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    9b0: 00060f93  addi         x31, x12, 0
    9b4: 00068f13  addi         x30, x13, 0
    9b8: 00070e93  addi         x29, x14, 0
    9bc: 330000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x000009c0
    9c0: 00148593  addi         x11, x9, 1
    9c4: 00058f93  addi         x31, x11, 0
    9c8: 568000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x000009cc
    9cc: 000a8613  addi         x12, x21, 0
    9d0: 000b0693  addi         x13, x22, 0
    9d4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    9d8: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    9dc: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    9e0: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    9e4: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    9e8: 00f70733  add          x14, x14, x15
    9ec: 00060f93  addi         x31, x12, 0
    9f0: 00068f13  addi         x30, x13, 0
    9f4: 00070e93  addi         x29, x14, 0
    9f8: 2f4000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x000009fc
    9fc: 00248593  addi         x11, x9, 2
    a00: 00058f93  addi         x31, x11, 0
    a04: 52c000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x00000a08
    a08: 000a8613  addi         x12, x21, 0
    a0c: 000b0693  addi         x13, x22, 0
    a10: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a14: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    a18: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    a1c: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a20: 00f70733  add          x14, x14, x15
    a24: 00060f93  addi         x31, x12, 0
    a28: 00068f13  addi         x30, x13, 0
    a2c: 00070e93  addi         x29, x14, 0
    a30: 2bc000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x00000a34
    a34: 00348593  addi         x11, x9, 3
    a38: 00058f93  addi         x31, x11, 0
    a3c: 4f4000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x00000a40
    a40: 000a8613  addi         x12, x21, 0
    a44: 000b0693  addi         x13, x22, 0
    a48: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a4c: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    a50: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    a54: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    a58: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    a5c: 00f70733  add          x14, x14, x15
    a60: 00060f93  addi         x31, x12, 0
    a64: 00068f13  addi         x30, x13, 0
    a68: 00070e93  addi         x29, x14, 0
    a6c: 280000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x00000a70
    a70: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    a74: 8ac80813  addi         x16, x16, -1876  # x16 = 0xffb008ac · riscv_local_mem + 0x8ac
    a78: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x8ac · 0xffb008ac
loc_a7c:
    a7c: ffb4a837  lui          x16, 0xffb4a  # x16 = 0xffb4a000
    a80: 02080813  addi         x16, x16, 32  # x16 = 0xffb4a020
    a84: 00085603  lhu          x12, 0(x16)  # 0xffb4a020
    a88: 40c586b3  sub          x13, x11, x12
    a8c: 01069693  slli         x13, x13, 16
    a90: 0106d693  srli         x13, x13, 16
    a94: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    a98: 40d70733  sub          x14, x14, x13
    a9c: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    aa0: 00f77663  bgeu         x14, x15, 0x00000aac  # target 0x00000aac
    aa4: 0ff0000f  fence        0xf, 0xf
    aa8: fd5ff06f  jal          x0, 0x00000a7c  # target 0x00000a7c
loc_aac:
    aac: 0ff0000f  fence        0xf, 0xf
    ab0: 00048593  addi         x11, x9, 0
    ab4: 00058f93  addi         x31, x11, 0
    ab8: 4c4000ef  jal          x1, 0x00000f7c  # target 0x00000f7c; x1 = 0x00000abc
    abc: 000a8613  addi         x12, x21, 0
    ac0: 000b0693  addi         x13, x22, 0
    ac4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    ac8: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    acc: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    ad0: 00060f93  addi         x31, x12, 0
    ad4: 00068f13  addi         x30, x13, 0
    ad8: 00070e93  addi         x29, x14, 0
    adc: 210000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x00000ae0
    ae0: 00148593  addi         x11, x9, 1
    ae4: 00058f93  addi         x31, x11, 0
    ae8: 494000ef  jal          x1, 0x00000f7c  # target 0x00000f7c; x1 = 0x00000aec
    aec: 000a8613  addi         x12, x21, 0
    af0: 000b0693  addi         x13, x22, 0
    af4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    af8: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    afc: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    b00: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    b04: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    b08: 00f70733  add          x14, x14, x15
    b0c: 00060f93  addi         x31, x12, 0
    b10: 00068f13  addi         x30, x13, 0
    b14: 00070e93  addi         x29, x14, 0
    b18: 1d4000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x00000b1c
    b1c: 00248593  addi         x11, x9, 2
    b20: 00058f93  addi         x31, x11, 0
    b24: 458000ef  jal          x1, 0x00000f7c  # target 0x00000f7c; x1 = 0x00000b28
    b28: 000a8613  addi         x12, x21, 0
    b2c: 000b0693  addi         x13, x22, 0
    b30: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b34: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    b38: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    b3c: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    b40: 00f70733  add          x14, x14, x15
    b44: 00060f93  addi         x31, x12, 0
    b48: 00068f13  addi         x30, x13, 0
    b4c: 00070e93  addi         x29, x14, 0
    b50: 19c000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x00000b54
    b54: 00348593  addi         x11, x9, 3
    b58: 00058f93  addi         x31, x11, 0
    b5c: 420000ef  jal          x1, 0x00000f7c  # target 0x00000f7c; x1 = 0x00000b60
    b60: 000a8613  addi         x12, x21, 0
    b64: 000b0693  addi         x13, x22, 0
    b68: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b6c: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    b70: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    b74: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    b78: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    b7c: 00f70733  add          x14, x14, x15
    b80: 00060f93  addi         x31, x12, 0
    b84: 00068f13  addi         x30, x13, 0
    b88: 00070e93  addi         x29, x14, 0
    b8c: 160000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x00000b90
    b90: 0f4000ef  jal          x1, 0x00000c84  # target 0x00000c84; x1 = 0x00000b94
    b94: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b98: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    b9c: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    ba0: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    ba4: 00c585b3  add          x11, x11, x12
    ba8: 000966b7  lui          x13, 0x00096  # x13 = 0x00096000
    bac: 00d5e663  bltu         x11, x13, 0x00000bb8  # target 0x00000bb8
    bb0: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    bb4: 40e585b3  sub          x11, x11, x14
loc_bb8:
    bb8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    bbc: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    bc0: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0; write runtime value
    bc4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    bc8: 8a460613  addi         x12, x12, -1884  # x12 = 0xffb008a4 · riscv_local_mem + 0x8a4
    bcc: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x8a4 · 0xffb008a4
    bd0: 00458593  addi         x11, x11, 4
    bd4: 01059593  slli         x11, x11, 16
    bd8: 0105d593  srli         x11, x11, 16
    bdc: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    be0: 8a460613  addi         x12, x12, -1884  # x12 = 0xffb008a4 · riscv_local_mem + 0x8a4
    be4: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x8a4 · 0xffb008a4; write runtime value
    be8: ffb49637  lui          x12, 0xffb49  # x12 = 0xffb49000
    bec: 02860613  addi         x12, x12, 40  # x12 = 0xffb49028
    bf0: 00b62023  sw           x11, 0(x12)  # 0xffb49028; write runtime value
    bf4: 0ff0000f  fence        0xf, 0xf
    bf8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    bfc: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    c00: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    c04: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    c08: 00c585b3  add          x11, x11, x12
    c0c: 0009a6b7  lui          x13, 0x0009a  # x13 = 0x0009a000
    c10: 00d5e663  bltu         x11, x13, 0x00000c1c  # target 0x00000c1c
    c14: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    c18: 40e585b3  sub          x11, x11, x14
loc_c1c:
    c1c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    c20: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    c24: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8; write runtime value
    c28: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    c2c: 8ac60613  addi         x12, x12, -1876  # x12 = 0xffb008ac · riscv_local_mem + 0x8ac
    c30: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x8ac · 0xffb008ac
    c34: 00458593  addi         x11, x11, 4
    c38: 01059593  slli         x11, x11, 16
    c3c: 0105d593  srli         x11, x11, 16
    c40: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    c44: 8ac60613  addi         x12, x12, -1876  # x12 = 0xffb008ac · riscv_local_mem + 0x8ac
    c48: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x8ac · 0xffb008ac; write runtime value
    c4c: ffb4a637  lui          x12, 0xffb4a  # x12 = 0xffb4a000
    c50: 02860613  addi         x12, x12, 40  # x12 = 0xffb4a028
    c54: 00b62023  sw           x11, 0(x12)  # 0xffb4a028; write runtime value
    c58: 0ff0000f  fence        0xf, 0xf
    c5c: 00138393  addi         x7, x7, 1
    c60: c31ff06f  jal          x0, 0x00000890  # target 0x00000890
loc_c64:
    c64: 3640006f  jal          x0, 0x00000fc8  # target 0x00000fc8
loc_c68:
    c68: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c6c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    c70: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    c74: 000a0463  beq          x20, x0, 0x00000c7c  # target 0x00000c7c
    c78: ff1ff06f  jal          x0, 0x00000c68  # target 0x00000c68
loc_c7c:
    c7c: 0ff0000f  fence        0xf, 0xf
    c80: 00008067  jalr         x0, 0(x1)
loc_c84:
    c84: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c88: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    c8c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    c90: 000a0463  beq          x20, x0, 0x00000c98  # target 0x00000c98
    c94: ff1ff06f  jal          x0, 0x00000c84  # target 0x00000c84
loc_c98:
    c98: 0ff0000f  fence        0xf, 0xf
    c9c: 00008067  jalr         x0, 0(x1)
loc_ca0:
    ca0: 7e400a93  addi         x21, x0, 2020  # x21 = 0x000007e4
    ca4: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_cos; 0x000007e4
    ca8: 007a7d13  andi         x26, x20, 7
    cac: ff8a7a13  andi         x20, x20, -8
    cb0: 01af8ab3  add          x21, x31, x26
    cb4: 007afb93  andi         x23, x21, 7
    cb8: 003ada93  srli         x21, x21, 3
    cbc: 00ba9a93  slli         x21, x21, 11
    cc0: 014a8ab3  add          x21, x21, x20
    cc4: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000cc4
    cc8: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000cdc
    ccc: 001b9b93  slli         x23, x23, 1
    cd0: 017b0b33  add          x22, x22, x23
    cd4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    cd8: 00008067  jalr         x0, 0(x1)
    cdc: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    ce0: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    ce4: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    ce8: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_cec:
    cec: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    cf0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    cf4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    cf8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    cfc: 015a6463  bltu         x20, x21, 0x00000d04  # target 0x00000d04
    d00: fedff06f  jal          x0, 0x00000cec  # target 0x00000cec
loc_d04:
    d04: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    d08: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    d0c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    d10: 014a1a13  slli         x20, x20, 20
    d14: 014a5a13  srli         x20, x20, 20
    d18: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_d1c:
    d1c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    d20: 000b0463  beq          x22, x0, 0x00000d28  # target 0x00000d28
    d24: ff9ff06f  jal          x0, 0x00000d1c  # target 0x00000d1c
loc_d28:
    d28: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    d2c: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    d30: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    d34: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    d38: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    d3c: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    d40: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    d44: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    d48: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    d4c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    d50: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    d54: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    d58: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    d5c: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    d60: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    d64: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    d68: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    d6c: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    d70: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    d74: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    d78: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    d7c: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_d80:
    d80: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    d84: 000b0463  beq          x22, x0, 0x00000d8c  # target 0x00000d8c
    d88: ff9ff06f  jal          x0, 0x00000d80  # target 0x00000d80
loc_d8c:
    d8c: 00008067  jalr         x0, 0(x1)
loc_d90:
    d90: 7e800a93  addi         x21, x0, 2024  # x21 = 0x000007e8
    d94: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_sin; 0x000007e8
    d98: 007a7d13  andi         x26, x20, 7
    d9c: ff8a7a13  andi         x20, x20, -8
    da0: 01af8ab3  add          x21, x31, x26
    da4: 007afb93  andi         x23, x21, 7
    da8: 003ada93  srli         x21, x21, 3
    dac: 00ba9a93  slli         x21, x21, 11
    db0: 014a8ab3  add          x21, x21, x20
    db4: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000db4
    db8: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000dcc
    dbc: 001b9b93  slli         x23, x23, 1
    dc0: 017b0b33  add          x22, x22, x23
    dc4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    dc8: 00008067  jalr         x0, 0(x1)
    dcc: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    dd0: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    dd4: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    dd8: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_ddc:
    ddc: 7d800a93  addi         x21, x0, 2008  # x21 = 0x000007d8
    de0: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_q_compact; 0x000007d8
    de4: 007a7d13  andi         x26, x20, 7
    de8: ff8a7a13  andi         x20, x20, -8
    dec: 01af8ab3  add          x21, x31, x26
    df0: 007afb93  andi         x23, x21, 7
    df4: 003ada93  srli         x21, x21, 3
    df8: 00ba9a93  slli         x21, x21, 11
    dfc: 014a8ab3  add          x21, x21, x20
    e00: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e00
    e04: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e18
    e08: 001b9b93  slli         x23, x23, 1
    e0c: 017b0b33  add          x22, x22, x23
    e10: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e14: 00008067  jalr         x0, 0(x1)
    e18: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    e1c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e20: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    e24: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_e28:
    e28: 7dc00a93  addi         x21, x0, 2012  # x21 = 0x000007dc
    e2c: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_k_compact; 0x000007dc
    e30: 007a7d13  andi         x26, x20, 7
    e34: ff8a7a13  andi         x20, x20, -8
    e38: 01af8ab3  add          x21, x31, x26
    e3c: 007afb93  andi         x23, x21, 7
    e40: 003ada93  srli         x21, x21, 3
    e44: 00ba9a93  slli         x21, x21, 11
    e48: 014a8ab3  add          x21, x21, x20
    e4c: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e4c
    e50: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e64
    e54: 001b9b93  slli         x23, x23, 1
    e58: 017b0b33  add          x22, x22, x23
    e5c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e60: 00008067  jalr         x0, 0(x1)
    e64: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    e68: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e6c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    e70: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_e74:
    e74: 7e000a93  addi         x21, x0, 2016  # x21 = 0x000007e0
    e78: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_v_compact; 0x000007e0
    e7c: 007a7d13  andi         x26, x20, 7
    e80: ff8a7a13  andi         x20, x20, -8
    e84: 01af8ab3  add          x21, x31, x26
    e88: 007afb93  andi         x23, x21, 7
    e8c: 003ada93  srli         x21, x21, 3
    e90: 00ba9a93  slli         x21, x21, 11
    e94: 014a8ab3  add          x21, x21, x20
    e98: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e98
    e9c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000eb0
    ea0: 001b9b93  slli         x23, x23, 1
    ea4: 017b0b33  add          x22, x22, x23
    ea8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    eac: 00008067  jalr         x0, 0(x1)
    eb0: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    eb4: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    eb8: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    ebc: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_ec0:
    ec0: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    ec4: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    ec8: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    ecc: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    ed0: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    ed4: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    ed8: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    edc: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    ee0: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    ee4: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    ee8: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    eec: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    ef0: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    ef4: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    ef8: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    efc: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    f00: 020f8f93  addi         x31, x31, 32
    f04: 020f0f13  addi         x30, x30, 32
    f08: ff8e8e93  addi         x29, x29, -8
    f0c: fa0e9ae3  bne          x29, x0, 0x00000ec0  # target 0x00000ec0
    f10: 00008067  jalr         x0, 0(x1)
loc_f14:
    f14: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    f18: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    f1c: 004f8f93  addi         x31, x31, 4
    f20: 004f0f13  addi         x30, x30, 4
    f24: fffe8e93  addi         x29, x29, -1
    f28: fe0e96e3  bne          x29, x0, 0x00000f14  # target 0x00000f14
    f2c: 00008067  jalr         x0, 0(x1)
loc_f30:
    f30: 7c400a93  addi         x21, x0, 1988  # x21 = 0x000007c4
    f34: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x000007c4
    f38: 007a7d13  andi         x26, x20, 7
    f3c: ff8a7a13  andi         x20, x20, -8
    f40: 01af8ab3  add          x21, x31, x26
    f44: 007afb93  andi         x23, x21, 7
    f48: 003ada93  srli         x21, x21, 3
    f4c: 00ba9a93  slli         x21, x21, 11
    f50: 014a8ab3  add          x21, x21, x20
    f54: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000f54
    f58: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000f6c
    f5c: 001b9b93  slli         x23, x23, 1
    f60: 017b0b33  add          x22, x22, x23
    f64: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    f68: 00008067  jalr         x0, 0(x1)
    f6c: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    f70: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    f74: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    f78: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_f7c:
    f7c: 7c800a93  addi         x21, x0, 1992  # x21 = 0x000007c8
    f80: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x000007c8
    f84: 007a7d13  andi         x26, x20, 7
    f88: ff8a7a13  andi         x20, x20, -8
    f8c: 01af8ab3  add          x21, x31, x26
    f90: 007afb93  andi         x23, x21, 7
    f94: 003ada93  srli         x21, x21, 3
    f98: 00ba9a93  slli         x21, x21, 11
    f9c: 014a8ab3  add          x21, x21, x20
    fa0: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000fa0
    fa4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000fb8
    fa8: 001b9b93  slli         x23, x23, 1
    fac: 017b0b33  add          x22, x22, x23
    fb0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    fb4: 00008067  jalr         x0, 0(x1)
    fb8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    fbc: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    fc0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    fc4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    fc8:           j FW_BRISC+4   # return to firmware, linked at install
