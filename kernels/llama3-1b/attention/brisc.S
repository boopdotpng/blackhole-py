# llama3 1b decode: attention, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (16): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=attention_core
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000182b7  lui          x5, 0x00018  # x5 = 0x00018000
      c: fc028293  addi         x5, x5, -64  # x5 = 0x00017fc0
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00017fc0
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     28: 0001a2b7  lui          x5, 0x0001a  # x5 = 0x0001a000
     2c: 7c028293  addi         x5, x5, 1984  # x5 = 0x0001a7c0
     30: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x0001a7c0
     34: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     38: 88420213  addi         x4, x4, -1916  # x4 = 0xffb00884 · riscv_local_mem + 0x884
     3c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     40: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     44: 88838393  addi         x7, x7, -1912  # x7 = 0xffb00888 · riscv_local_mem + 0x888
     48: 00016437  lui          x8, 0x00016  # x8 = 0x00016000
     4c: fc040413  addi         x8, x8, -64  # x8 = 0x00015fc0
     50: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x888 · 0xffb00888; write 0x00015fc0
     54: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     58: 88c38393  addi         x7, x7, -1908  # x7 = 0xffb0088c · riscv_local_mem + 0x88c
     5c: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x88c · 0xffb0088c; write 0x00000000
     60: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     64: 89038393  addi         x7, x7, -1904  # x7 = 0xffb00890 · riscv_local_mem + 0x890
     68: 00015437  lui          x8, 0x00015  # x8 = 0x00015000
     6c: fc040413  addi         x8, x8, -64  # x8 = 0x00014fc0
     70: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x890 · 0xffb00890; write 0x00014fc0
     74: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     78: 89438393  addi         x7, x7, -1900  # x7 = 0xffb00894 · riscv_local_mem + 0x894
     7c: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x894 · 0xffb00894; write 0x00000000
     80: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     84: 89848493  addi         x9, x9, -1896  # x9 = 0xffb00898 · riscv_local_mem + 0x898
     88: 0000f537  lui          x10, 0x0000f  # x10 = 0x0000f000
     8c: fc050513  addi         x10, x10, -64  # x10 = 0x0000efc0
     90: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x898 · 0xffb00898; write 0x0000efc0
     94: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     98: 89c48493  addi         x9, x9, -1892  # x9 = 0xffb0089c · riscv_local_mem + 0x89c
     9c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x89c · 0xffb0089c; write 0x00000000
     a0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     a4: 8a058593  addi         x11, x11, -1888  # x11 = 0xffb008a0 · riscv_local_mem + 0x8a0
     a8: 00010637  lui          x12, 0x00010  # x12 = 0x00010000
     ac: fc060613  addi         x12, x12, -64  # x12 = 0x0000ffc0
     b0: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x8a0 · 0xffb008a0; write 0x0000ffc0
     b4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     b8: 8a458593  addi         x11, x11, -1884  # x11 = 0xffb008a4 · riscv_local_mem + 0x8a4
     bc: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x8a4 · 0xffb008a4; write 0x00000000
     c0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     c4: 8a858593  addi         x11, x11, -1880  # x11 = 0xffb008a8 · riscv_local_mem + 0x8a8
     c8: 00012637  lui          x12, 0x00012  # x12 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     cc: fc060613  addi         x12, x12, -64  # x12 = 0x00011fc0
     d0: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x8a8 · 0xffb008a8; write 0x00011fc0
     d4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     d8: 8ac58593  addi         x11, x11, -1876  # x11 = 0xffb008ac · riscv_local_mem + 0x8ac
     dc: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x8ac · 0xffb008ac; write 0x00000000
     e0: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
     e4: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
     e8: 00425293  srli         x5, x4, 4
     ec: 00f27313  andi         x6, x4, 15
     f0: 00631313  slli         x6, x6, 6
     f4: 00131313  slli         x6, x6, 1
     f8: 319000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x000000fc
     fc: 331000ef  jal          x1, 0x00000c2c  # target 0x00000c2c; x1 = 0x00000100
    100: 00028f93  addi         x31, x5, 0
    104: 345000ef  jal          x1, 0x00000c48  # target 0x00000c48; x1 = 0x00000108
    108: 000a8393  addi         x7, x21, 0
    10c: 000b0413  addi         x8, x22, 0
    110: 00038f93  addi         x31, x7, 0
    114: 00040f13  addi         x30, x8, 0
    118: 0002feb7  lui          x29, 0x0002f  # x29 = 0x0002f000
    11c: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x0002f7c0
    120: 375000ef  jal          x1, 0x00000c94  # target 0x00000c94; x1 = 0x00000124
    124: 00028f93  addi         x31, x5, 0
    128: 411000ef  jal          x1, 0x00000d38  # target 0x00000d38; x1 = 0x0000012c
    12c: 000a8393  addi         x7, x21, 0
    130: 000b0413  addi         x8, x22, 0
    134: 00038f93  addi         x31, x7, 0
    138: 00040f13  addi         x30, x8, 0
    13c: 00030eb7  lui          x29, 0x00030  # x29 = 0x00030000 · arc_apb_reset_unit + 0x0
    140: fc0e8e93  addi         x29, x29, -64  # x29 = 0x0002ffc0
    144: 351000ef  jal          x1, 0x00000c94  # target 0x00000c94; x1 = 0x00000148
    148: 2e5000ef  jal          x1, 0x00000c2c  # target 0x00000c2c; x1 = 0x0000014c
    14c: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    150: 90048493  addi         x9, x9, -1792  # x9 = 0x0000e900
    154: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x0000e900
    158: 00741413  slli         x8, x8, 7
    15c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
loc_160:
    160: 24000693  addi         x13, x0, 576  # x13 = 0x00000240
    164: 00d47c63  bgeu         x8, x13, 0x0000017c  # target 0x0000017c
    168: 01800613  addi         x12, x0, 24  # x12 = 0x00000018
    16c: 02c454b3  divu         x9, x8, x12
    170: 02c485b3  mul          x11, x9, x12
    174: 40b405b3  sub          x11, x8, x11
    178: 01c0006f  jal          x0, 0x00000194  # target 0x00000194
loc_17c:
    17c: 40d406b3  sub          x13, x8, x13
    180: 01700613  addi         x12, x0, 23  # x12 = 0x00000017
    184: 02c6d4b3  divu         x9, x13, x12
    188: 02c485b3  mul          x11, x9, x12
    18c: 40b685b3  sub          x11, x13, x11
    190: 01848493  addi         x9, x9, 24
loc_194:
    194: 03f40513  addi         x10, x8, 63
    198: 24000793  addi         x15, x0, 576  # x15 = 0x00000240
    19c: 00f57c63  bgeu         x10, x15, 0x000001b4  # target 0x000001b4
    1a0: 01800713  addi         x14, x0, 24  # x14 = 0x00000018
    1a4: 02e55633  divu         x12, x10, x14
    1a8: 02e606b3  mul          x13, x12, x14
    1ac: 40d506b3  sub          x13, x10, x13
    1b0: 01c0006f  jal          x0, 0x000001cc  # target 0x000001cc
loc_1b4:
    1b4: 40f507b3  sub          x15, x10, x15
    1b8: 01700713  addi         x14, x0, 23  # x14 = 0x00000017
    1bc: 02e7d633  divu         x12, x15, x14
    1c0: 02e606b3  mul          x13, x12, x14
    1c4: 40d786b3  sub          x13, x15, x13
    1c8: 01860613  addi         x12, x12, 24
loc_1cc:
    1cc: 00048513  addi         x10, x9, 0
    1d0: 241000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x000001d4
    1d4: 259000ef  jal          x1, 0x00000c2c  # target 0x00000c2c; x1 = 0x000001d8
    1d8: 0001b737  lui          x14, 0x0001b  # x14 = 0x0001b000
    1dc: fc070713  addi         x14, x14, -64  # x14 = 0x0001afc0
loc_1e0:
    1e0: 00050f93  addi         x31, x10, 0
    1e4: 3a1000ef  jal          x1, 0x00000d84  # target 0x00000d84; x1 = 0x000001e8
    1e8: 000a8793  addi         x15, x21, 0
    1ec: 000b0813  addi         x16, x22, 0
    1f0: 00078f93  addi         x31, x15, 0
    1f4: 00080f13  addi         x30, x16, 0
    1f8: 00070e93  addi         x29, x14, 0
    1fc: 299000ef  jal          x1, 0x00000c94  # target 0x00000c94; x1 = 0x00000200
    200: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    204: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    208: 00f70733  add          x14, x14, x15
    20c: 00150513  addi         x10, x10, 1
    210: fca678e3  bgeu         x12, x10, 0x000001e0  # target 0x000001e0
    214: 219000ef  jal          x1, 0x00000c2c  # target 0x00000c2c; x1 = 0x00000218
    218: 00048513  addi         x10, x9, 0
    21c: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    220: 00739693  slli         x13, x7, 7
    224: 00018737  lui          x14, 0x00018  # x14 = 0x00018000
    228: fc070713  addi         x14, x14, -64  # x14 = 0x00017fc0
    22c: 00e686b3  add          x13, x13, x14
loc_230:
    230: 01700713  addi         x14, x0, 23  # x14 = 0x00000017
    234: 01800793  addi         x15, x0, 24  # x15 = 0x00000018
    238: 00f57463  bgeu         x10, x15, 0x00000240  # target 0x00000240
    23c: 00170713  addi         x14, x14, 1  # x14 = 0x00000018
loc_240:
    240: 40b70733  sub          x14, x14, x11
    244: 00f5f793  andi         x15, x11, 15
    248: 40f007b3  sub          x15, x0, x15
    24c: 01078793  addi         x15, x15, 16
    250: 00e7f463  bgeu         x15, x14, 0x00000258  # target 0x00000258
    254: 00078713  addi         x14, x15, 0
loc_258:
    258: 01f67793  andi         x15, x12, 31
    25c: 40f007b3  sub          x15, x0, x15
    260: 02078793  addi         x15, x15, 32
    264: 00e7f463  bgeu         x15, x14, 0x0000026c  # target 0x0000026c
    268: 00078713  addi         x14, x15, 0
loc_26c:
    26c: 40950833  sub          x16, x10, x9
    270: 00b81813  slli         x16, x16, 11
    274: 00f5f793  andi         x15, x11, 15
    278: 00179793  slli         x15, x15, 1
    27c: 0105fa13  andi         x20, x11, 16
    280: 005a1a13  slli         x20, x20, 5
    284: 0147e7b3  or           x15, x15, x20
    288: 1e05fa13  andi         x20, x11, 480
    28c: 0147e7b3  or           x15, x15, x20
    290: 0095da13  srli         x20, x11, 9
    294: 00aa1a13  slli         x20, x20, 10
    298: 0147e7b3  or           x15, x15, x20
    29c: 00f80833  add          x16, x16, x15
    2a0: 0001ba37  lui          x20, 0x0001b  # x20 = 0x0001b000
    2a4: fc0a0a13  addi         x20, x20, -64  # x20 = 0x0001afc0
    2a8: 01480833  add          x16, x16, x20
    2ac: 00161893  slli         x17, x12, 1
    2b0: 00d888b3  add          x17, x17, x13
    2b4: 02064913  xori         x18, x12, 32
    2b8: 00191913  slli         x18, x18, 1
    2bc: 00d90933  add          x18, x18, x13
    2c0: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2c4: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    2c8: 01490933  add          x18, x18, x20
    2cc: 02067993  andi         x19, x12, 32
    2d0: 00a99993  slli         x19, x19, 10
    2d4: 00080f93  addi         x31, x16, 0
    2d8: 00088f13  addi         x30, x17, 0
    2dc: 00090e93  addi         x29, x18, 0
    2e0: 00070e13  addi         x28, x14, 0
    2e4: 00098d93  addi         x27, x19, 0
loc_2e8:
    2e8: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    2ec: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    2f0: 01ba4a33  xor          x20, x20, x27
    2f4: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    2f8: 002f8f93  addi         x31, x31, 2
    2fc: 002f0f13  addi         x30, x30, 2
    300: 002e8e93  addi         x29, x29, 2
    304: fffe0e13  addi         x28, x28, -1
    308: fe0e10e3  bne          x28, x0, 0x000002e8  # target 0x000002e8
    30c: 00e60633  add          x12, x12, x14
    310: 00e585b3  add          x11, x11, x14
    314: 01700793  addi         x15, x0, 23  # x15 = 0x00000017
    318: 01800993  addi         x19, x0, 24  # x19 = 0x00000018
    31c: 01357463  bgeu         x10, x19, 0x00000324  # target 0x00000324
    320: 00178793  addi         x15, x15, 1  # x15 = 0x00000018
loc_324:
    324: 00f59663  bne          x11, x15, 0x00000330  # target 0x00000330
    328: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    32c: 00150513  addi         x10, x10, 1
loc_330:
    330: 04000793  addi         x15, x0, 64  # x15 = 0x00000040
    334: eef66ee3  bltu         x12, x15, 0x00000230  # target 0x00000230
    338: 04040413  addi         x8, x8, 64
    33c: 00138393  addi         x7, x7, 1
    340: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    344: e0939ee3  bne          x7, x9, 0x00000160  # target 0x00000160
    348: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    34c: 90048493  addi         x9, x9, -1792  # x9 = 0x0000e900
    350: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x0000e900
    354: 00145413  srli         x8, x8, 1
    358: 00641413  slli         x8, x8, 6
    35c: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
    360: 1b000693  addi         x13, x0, 432  # x13 = 0x000001b0
    364: 00d47c63  bgeu         x8, x13, 0x0000037c  # target 0x0000037c
    368: 00600613  addi         x12, x0, 6  # x12 = 0x00000006
    36c: 02c454b3  divu         x9, x8, x12
    370: 02c485b3  mul          x11, x9, x12
    374: 40b405b3  sub          x11, x8, x11
    378: 01c0006f  jal          x0, 0x00000394  # target 0x00000394
loc_37c:
    37c: 40d406b3  sub          x13, x8, x13
    380: 00500613  addi         x12, x0, 5  # x12 = 0x00000005
    384: 02c6d4b3  divu         x9, x13, x12
    388: 02c485b3  mul          x11, x9, x12
    38c: 40b685b3  sub          x11, x13, x11
    390: 04848493  addi         x9, x9, 72
loc_394:
    394: 03f40513  addi         x10, x8, 63
    398: 1b000793  addi         x15, x0, 432  # x15 = 0x000001b0
    39c: 00f57c63  bgeu         x10, x15, 0x000003b4  # target 0x000003b4
    3a0: 00600713  addi         x14, x0, 6  # x14 = 0x00000006
    3a4: 02e55633  divu         x12, x10, x14
    3a8: 02e606b3  mul          x13, x12, x14
    3ac: 40d506b3  sub          x13, x10, x13
    3b0: 01c0006f  jal          x0, 0x000003cc  # target 0x000003cc
loc_3b4:
    3b4: 40f507b3  sub          x15, x10, x15
    3b8: 00500713  addi         x14, x0, 5  # x14 = 0x00000005
    3bc: 02e7d633  divu         x12, x15, x14
    3c0: 02e606b3  mul          x13, x12, x14
    3c4: 40d786b3  sub          x13, x15, x13
    3c8: 04860613  addi         x12, x12, 72
loc_3cc:
    3cc: 00048513  addi         x10, x9, 0
    3d0: 041000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x000003d4
    3d4: 059000ef  jal          x1, 0x00000c2c  # target 0x00000c2c; x1 = 0x000003d8
    3d8: 0001b737  lui          x14, 0x0001b  # x14 = 0x0001b000
    3dc: fc070713  addi         x14, x14, -64  # x14 = 0x0001afc0
loc_3e0:
    3e0: 00050f93  addi         x31, x10, 0
    3e4: 1ed000ef  jal          x1, 0x00000dd0  # target 0x00000dd0; x1 = 0x000003e8
    3e8: 000a8793  addi         x15, x21, 0
    3ec: 000b0813  addi         x16, x22, 0
    3f0: 00078f93  addi         x31, x15, 0
    3f4: 00080f13  addi         x30, x16, 0
    3f8: 00070e93  addi         x29, x14, 0
    3fc: 099000ef  jal          x1, 0x00000c94  # target 0x00000c94; x1 = 0x00000400
    400: 00050f93  addi         x31, x10, 0
    404: 219000ef  jal          x1, 0x00000e1c  # target 0x00000e1c; x1 = 0x00000408
    408: 000a8793  addi         x15, x21, 0
    40c: 000b0813  addi         x16, x22, 0
    410: 0000a8b7  lui          x17, 0x0000a  # x17 = 0x0000a000
    414: 00e888b3  add          x17, x17, x14
    418: 00078f93  addi         x31, x15, 0
    41c: 00080f13  addi         x30, x16, 0
    420: 00088e93  addi         x29, x17, 0
    424: 071000ef  jal          x1, 0x00000c94  # target 0x00000c94; x1 = 0x00000428
    428: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    42c: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    430: 00f70733  add          x14, x14, x15
    434: 00150513  addi         x10, x10, 1
    438: faa674e3  bgeu         x12, x10, 0x000003e0  # target 0x000003e0
    43c: 7f0000ef  jal          x1, 0x00000c2c  # target 0x00000c2c; x1 = 0x00000440
    440: 00048513  addi         x10, x9, 0
    444: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    448: 00739693  slli         x13, x7, 7
    44c: 00018737  lui          x14, 0x00018  # x14 = 0x00018000
    450: fc070713  addi         x14, x14, -64  # x14 = 0x00017fc0
    454: 00e686b3  add          x13, x13, x14
loc_458:
    458: 00500713  addi         x14, x0, 5  # x14 = 0x00000005
    45c: 04800793  addi         x15, x0, 72  # x15 = 0x00000048
    460: 00f57463  bgeu         x10, x15, 0x00000468  # target 0x00000468
    464: 00170713  addi         x14, x14, 1  # x14 = 0x00000006
loc_468:
    468: 40b70733  sub          x14, x14, x11
    46c: 00f5f793  andi         x15, x11, 15
    470: 40f007b3  sub          x15, x0, x15
    474: 01078793  addi         x15, x15, 16
    478: 00e7f463  bgeu         x15, x14, 0x00000480  # target 0x00000480
    47c: 00078713  addi         x14, x15, 0
loc_480:
    480: 01f67793  andi         x15, x12, 31
    484: 40f007b3  sub          x15, x0, x15
    488: 02078793  addi         x15, x15, 32
    48c: 00e7f463  bgeu         x15, x14, 0x00000494  # target 0x00000494
    490: 00078713  addi         x14, x15, 0
loc_494:
    494: 40950833  sub          x16, x10, x9
    498: 00b81813  slli         x16, x16, 11
    49c: 00f5f793  andi         x15, x11, 15
    4a0: 00179793  slli         x15, x15, 1
    4a4: 0105fa13  andi         x20, x11, 16
    4a8: 005a1a13  slli         x20, x20, 5
    4ac: 0147e7b3  or           x15, x15, x20
    4b0: 1e05fa13  andi         x20, x11, 480
    4b4: 0147e7b3  or           x15, x15, x20
    4b8: 0095da13  srli         x20, x11, 9
    4bc: 00aa1a13  slli         x20, x20, 10
    4c0: 0147e7b3  or           x15, x15, x20
    4c4: 00f80833  add          x16, x16, x15
    4c8: 0001ba37  lui          x20, 0x0001b  # x20 = 0x0001b000
    4cc: fc0a0a13  addi         x20, x20, -64  # x20 = 0x0001afc0
    4d0: 01480833  add          x16, x16, x20
    4d4: 00161893  slli         x17, x12, 1
    4d8: 00d888b3  add          x17, x17, x13
    4dc: 02064913  xori         x18, x12, 32
    4e0: 00191913  slli         x18, x18, 1
    4e4: 00d90933  add          x18, x18, x13
    4e8: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4ec: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    4f0: 01490933  add          x18, x18, x20
    4f4: 02067993  andi         x19, x12, 32
    4f8: 00a99993  slli         x19, x19, 10
    4fc: 0000aa37  lui          x20, 0x0000a  # x20 = 0x0000a000
    500: 010a0a33  add          x20, x20, x16
    504: 00161a93  slli         x21, x12, 1
    508: 0002fb37  lui          x22, 0x0002f  # x22 = 0x0002f000
    50c: fc0b0b13  addi         x22, x22, -64  # x22 = 0x0002efc0
    510: 016a8ab3  add          x21, x21, x22
    514: ffc10113  addi         x2, x2, -4
    518: 01412023  sw           x20, 0(x2)  # Address depends on runtime register values
    51c: 00080f93  addi         x31, x16, 0
    520: 00088f13  addi         x30, x17, 0
    524: 00090e93  addi         x29, x18, 0
    528: 00070e13  addi         x28, x14, 0
    52c: 00098d93  addi         x27, x19, 0
    530: 000a0d13  addi         x26, x20, 0
    534: 000a8c93  addi         x25, x21, 0
loc_538:
    538: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    53c: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    540: 01ba4a33  xor          x20, x20, x27
    544: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    548: 000d5a03  lhu          x20, 0(x26)  # Address depends on runtime register values
    54c: 014c9023  sh           x20, 0(x25)  # Address depends on runtime register values
    550: 002d0d13  addi         x26, x26, 2
    554: 002c8c93  addi         x25, x25, 2
    558: 002f8f93  addi         x31, x31, 2
    55c: 002f0f13  addi         x30, x30, 2
    560: 002e8e93  addi         x29, x29, 2
    564: fffe0e13  addi         x28, x28, -1
    568: fc0e18e3  bne          x28, x0, 0x00000538  # target 0x00000538
    56c: 00012a03  lw           x20, 0(x2)  # Address depends on runtime register values
    570: 00410113  addi         x2, x2, 4
    574: 00e60633  add          x12, x12, x14
    578: 00e585b3  add          x11, x11, x14
    57c: 00500793  addi         x15, x0, 5  # x15 = 0x00000005
    580: 04800993  addi         x19, x0, 72  # x19 = 0x00000048
    584: 01357463  bgeu         x10, x19, 0x0000058c  # target 0x0000058c
    588: 00178793  addi         x15, x15, 1  # x15 = 0x00000006
loc_58c:
    58c: 00f59663  bne          x11, x15, 0x00000598  # target 0x00000598
    590: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    594: 00150513  addi         x10, x10, 1
loc_598:
    598: 04000793  addi         x15, x0, 64  # x15 = 0x00000040
    59c: eaf66ee3  bltu         x12, x15, 0x00000458  # target 0x00000458
    5a0: 0002f3b7  lui          x7, 0x0002f  # x7 = 0x0002f000
    5a4: 7c038393  addi         x7, x7, 1984  # x7 = 0x0002f7c0
    5a8: 006383b3  add          x7, x7, x6
    5ac: 00038f93  addi         x31, x7, 0
    5b0: 00019f37  lui          x30, 0x00019  # x30 = 0x00019000
    5b4: fc0f0f13  addi         x30, x30, -64  # x30 = 0x00018fc0
    5b8: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    5bc: 0ad000ef  jal          x1, 0x00000e68  # target 0x00000e68; x1 = 0x000005c0
    5c0: 00019fb7  lui          x31, 0x00019  # x31 = 0x00019000
    5c4: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00018fc0
    5c8: 00019f37  lui          x30, 0x00019  # x30 = 0x00019000
    5cc: 040f0f13  addi         x30, x30, 64  # x30 = 0x00019040
    5d0: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    5d4: 0e9000ef  jal          x1, 0x00000ebc  # target 0x00000ebc; x1 = 0x000005d8
    5d8: 00019fb7  lui          x31, 0x00019  # x31 = 0x00019000
    5dc: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00018fc0
    5e0: 00019f37  lui          x30, 0x00019  # x30 = 0x00019000
    5e4: 0c0f0f13  addi         x30, x30, 192  # x30 = 0x000190c0
    5e8: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    5ec: 0d1000ef  jal          x1, 0x00000ebc  # target 0x00000ebc; x1 = 0x000005f0
    5f0: 000303b7  lui          x7, 0x00030  # x7 = 0x00030000 · arc_apb_reset_unit + 0x0
    5f4: fc038393  addi         x7, x7, -64  # x7 = 0x0002ffc0
    5f8: 006383b3  add          x7, x7, x6
    5fc: 00038f93  addi         x31, x7, 0
    600: 00019f37  lui          x30, 0x00019  # x30 = 0x00019000
    604: 7c0f0f13  addi         x30, x30, 1984  # x30 = 0x000197c0
    608: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    60c: 05d000ef  jal          x1, 0x00000e68  # target 0x00000e68; x1 = 0x00000610
    610: 00019fb7  lui          x31, 0x00019  # x31 = 0x00019000
    614: 7c0f8f93  addi         x31, x31, 1984  # x31 = 0x000197c0
    618: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    61c: 840f0f13  addi         x30, x30, -1984  # x30 = 0x00019840
    620: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    624: 099000ef  jal          x1, 0x00000ebc  # target 0x00000ebc; x1 = 0x00000628
    628: 00019fb7  lui          x31, 0x00019  # x31 = 0x00019000
    62c: 7c0f8f93  addi         x31, x31, 1984  # x31 = 0x000197c0
    630: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    634: 8c0f0f13  addi         x30, x30, -1856  # x30 = 0x000198c0
    638: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    63c: 081000ef  jal          x1, 0x00000ebc  # target 0x00000ebc; x1 = 0x00000640
    640: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    644: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    648: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    64c: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    650: 00520233  add          x4, x4, x5
    654: 0001a337  lui          x6, 0x0001a  # x6 = 0x0001a000
    658: fc030313  addi         x6, x6, -64  # x6 = 0x00019fc0
    65c: 00626663  bltu         x4, x6, 0x00000668  # target 0x00000668
    660: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    664: 40720233  sub          x4, x4, x7
loc_668:
    668: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    66c: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    670: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    674: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    678: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    67c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    680: 00420213  addi         x4, x4, 4
    684: 01021213  slli         x4, x4, 16
    688: 01025213  srli         x4, x4, 16
    68c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    690: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    694: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    698: ffb4f2b7  lui          x5, 0xffb4f  # x5 = 0xffb4f000
    69c: 02828293  addi         x5, x5, 40  # x5 = 0xffb4f028
    6a0: 0042a023  sw           x4, 0(x5)  # 0xffb4f028; write runtime value
    6a4: 0ff0000f  fence        0xf, 0xf
    6a8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6ac: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
    6b0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884
    6b4: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_6b8:
    6b8: ffb51437  lui          x8, 0xffb51  # x8 = 0xffb51000
    6bc: 02840413  addi         x8, x8, 40  # x8 = 0xffb51028
    6c0: 00045283  lhu          x5, 0(x8)  # 0xffb51028
    6c4: 40428333  sub          x6, x5, x4
    6c8: 01031313  slli         x6, x6, 16
    6cc: 01035313  srli         x6, x6, 16
    6d0: 00737663  bgeu         x6, x7, 0x000006dc  # target 0x000006dc
    6d4: 0ff0000f  fence        0xf, 0xf
    6d8: fe1ff06f  jal          x0, 0x000006b8  # target 0x000006b8
loc_6dc:
    6dc: 0ff0000f  fence        0xf, 0xf
    6e0: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
    6e4: 90038393  addi         x7, x7, -1792  # x7 = 0x0000e900
    6e8: 0003a203  lw           x4, 0(x7)  # param attention_core; 0x0000e900
    6ec: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    6f0: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000790
    6f4: 79400393  addi         x7, x0, 1940  # x7 = 0x00000794
    6f8: 0003a303  lw           x6, 0(x7)  # param valid_columns; 0x00000794
    6fc: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    700: 88c60613  addi         x12, x12, -1908  # x12 = 0xffb0088c · riscv_local_mem + 0x88c
    704: 00062383  lw           x7, 0(x12)  # riscv_local_mem + 0x88c · 0xffb0088c
loc_708:
    708: ffb4d637  lui          x12, 0xffb4d  # x12 = 0xffb4d000
    70c: 02060613  addi         x12, x12, 32  # x12 = 0xffb4d020
    710: 00065403  lhu          x8, 0(x12)  # 0xffb4d020
    714: 408384b3  sub          x9, x7, x8
    718: 01049493  slli         x9, x9, 16
    71c: 0104d493  srli         x9, x9, 16
    720: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
    724: 40950533  sub          x10, x10, x9
    728: 00100593  addi         x11, x0, 1  # x11 = 0x00000001
    72c: 00b57663  bgeu         x10, x11, 0x00000738  # target 0x00000738
    730: 0ff0000f  fence        0xf, 0xf
    734: fd5ff06f  jal          x0, 0x00000708  # target 0x00000708
loc_738:
    738: 0ff0000f  fence        0xf, 0xf
    73c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    740: 88840413  addi         x8, x8, -1912  # x8 = 0xffb00888 · riscv_local_mem + 0x888
    744: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x888 · 0xffb00888
    748: 00038413  addi         x8, x7, 0
    74c: 40000493  addi         x9, x0, 1024  # x9 = 0x00000400
loc_750:
    750: 00042023  sw           x0, 0(x8)  # Address depends on runtime register values
    754: 00042223  sw           x0, 4(x8)  # Address depends on runtime register values
    758: 00042423  sw           x0, 8(x8)  # Address depends on runtime register values
    75c: 00042623  sw           x0, 12(x8)  # Address depends on runtime register values
    760: 00042823  sw           x0, 16(x8)  # Address depends on runtime register values
    764: 00042a23  sw           x0, 20(x8)  # Address depends on runtime register values
    768: 00042c23  sw           x0, 24(x8)  # Address depends on runtime register values
    76c: 00042e23  sw           x0, 28(x8)  # Address depends on runtime register values
    770: 02040413  addi         x8, x8, 32
    774: ff848493  addi         x9, x9, -8
    778: fc049ce3  bne          x9, x0, 0x00000750  # target 0x00000750
    77c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    780: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    784: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888
    788: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    78c: 008383b3  add          x7, x7, x8
    790: 000174b7  lui          x9, 0x00017  # x9 = 0x00017000
    794: fc048493  addi         x9, x9, -64  # x9 = 0x00016fc0
    798: 0093e663  bltu         x7, x9, 0x000007a4  # target 0x000007a4
    79c: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7a0: 40a383b3  sub          x7, x7, x10
loc_7a4:
    7a4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    7a8: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    7ac: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
    7b0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7b4: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    7b8: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c
    7bc: 00138393  addi         x7, x7, 1
    7c0: 01039393  slli         x7, x7, 16
    7c4: 0103d393  srli         x7, x7, 16
    7c8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7cc: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    7d0: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c; write runtime value
    7d4: ffb4d437  lui          x8, 0xffb4d  # x8 = 0xffb4d000
    7d8: 02840413  addi         x8, x8, 40  # x8 = 0xffb4d028
    7dc: 00742023  sw           x7, 0(x8)  # 0xffb4d028; write runtime value
    7e0: 0ff0000f  fence        0xf, 0xf
    7e4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    7e8: 89460613  addi         x12, x12, -1900  # x12 = 0xffb00894 · riscv_local_mem + 0x894
    7ec: 00062383  lw           x7, 0(x12)  # riscv_local_mem + 0x894 · 0xffb00894
loc_7f0:
    7f0: ffb4c637  lui          x12, 0xffb4c  # x12 = 0xffb4c000
    7f4: 02060613  addi         x12, x12, 32  # x12 = 0xffb4c020
    7f8: 00065403  lhu          x8, 0(x12)  # 0xffb4c020
    7fc: 408384b3  sub          x9, x7, x8
    800: 01049493  slli         x9, x9, 16
    804: 0104d493  srli         x9, x9, 16
    808: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
    80c: 40950533  sub          x10, x10, x9
    810: 00100593  addi         x11, x0, 1  # x11 = 0x00000001
    814: 00b57663  bgeu         x10, x11, 0x00000820  # target 0x00000820
    818: 0ff0000f  fence        0xf, 0xf
    81c: fd5ff06f  jal          x0, 0x000007f0  # target 0x000007f0
loc_820:
    820: 0ff0000f  fence        0xf, 0xf
    824: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    828: 89040413  addi         x8, x8, -1904  # x8 = 0xffb00890 · riscv_local_mem + 0x890
    82c: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x890 · 0xffb00890
    830: 00038413  addi         x8, x7, 0
    834: 40000493  addi         x9, x0, 1024  # x9 = 0x00000400
loc_838:
    838: 00042023  sw           x0, 0(x8)  # Address depends on runtime register values
    83c: 00042223  sw           x0, 4(x8)  # Address depends on runtime register values
    840: 00042423  sw           x0, 8(x8)  # Address depends on runtime register values
    844: 00042623  sw           x0, 12(x8)  # Address depends on runtime register values
    848: 00042823  sw           x0, 16(x8)  # Address depends on runtime register values
    84c: 00042a23  sw           x0, 20(x8)  # Address depends on runtime register values
    850: 00042c23  sw           x0, 24(x8)  # Address depends on runtime register values
    854: 00042e23  sw           x0, 28(x8)  # Address depends on runtime register values
    858: 02040413  addi         x8, x8, 32
    85c: ff848493  addi         x9, x9, -8
    860: fc049ce3  bne          x9, x0, 0x00000838  # target 0x00000838
    864: 00030413  addi         x8, x6, 0
    868: 02000493  addi         x9, x0, 32  # x9 = 0x00000020
    86c: ff800537  lui          x10, 0xff800  # x10 = 0xff800000
loc_870:
    870: 02947a63  bgeu         x8, x9, 0x000008a4  # target 0x000008a4
    874: 00445593  srli         x11, x8, 4
    878: 00a59593  slli         x11, x11, 10
    87c: 00f47613  andi         x12, x8, 15
    880: 00261613  slli         x12, x12, 2
    884: 00c586b3  add          x13, x11, x12
    888: 00d38733  add          x14, x7, x13
    88c: 00a72023  sw           x10, 0(x14)  # Address depends on runtime register values
    890: 00d38733  add          x14, x7, x13
    894: 04070713  addi         x14, x14, 64
    898: 00a72023  sw           x10, 0(x14)  # Address depends on runtime register values
    89c: 00140413  addi         x8, x8, 1
    8a0: fd1ff06f  jal          x0, 0x00000870  # target 0x00000870
loc_8a4:
    8a4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    8a8: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
    8ac: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890
    8b0: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8b4: 008383b3  add          x7, x7, x8
    8b8: 000164b7  lui          x9, 0x00016  # x9 = 0x00016000
    8bc: fc048493  addi         x9, x9, -64  # x9 = 0x00015fc0
    8c0: 0093e663  bltu         x7, x9, 0x000008cc  # target 0x000008cc
    8c4: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8c8: 40a383b3  sub          x7, x7, x10
loc_8cc:
    8cc: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    8d0: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
    8d4: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890; write runtime value
    8d8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    8dc: 89440413  addi         x8, x8, -1900  # x8 = 0xffb00894 · riscv_local_mem + 0x894
    8e0: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x894 · 0xffb00894
    8e4: 00138393  addi         x7, x7, 1
    8e8: 01039393  slli         x7, x7, 16
    8ec: 0103d393  srli         x7, x7, 16
    8f0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    8f4: 89440413  addi         x8, x8, -1900  # x8 = 0xffb00894 · riscv_local_mem + 0x894
    8f8: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x894 · 0xffb00894; write runtime value
    8fc: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    900: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    904: 00742023  sw           x7, 0(x8)  # 0xffb4c028; write runtime value
    908: 0ff0000f  fence        0xf, 0xf
    90c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    910: 00028413  addi         x8, x5, 0
loc_914:
    914: 2e83fc63  bgeu         x7, x8, 0x00000c0c  # target 0x00000c0c
    918: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    91c: 89c70713  addi         x14, x14, -1892  # x14 = 0xffb0089c · riscv_local_mem + 0x89c
    920: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x89c · 0xffb0089c
loc_924:
    924: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    928: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    92c: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    930: 40a485b3  sub          x11, x9, x10
    934: 01059593  slli         x11, x11, 16
    938: 0105d593  srli         x11, x11, 16
    93c: 00200613  addi         x12, x0, 2  # x12 = 0x00000002
    940: 40b60633  sub          x12, x12, x11
    944: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    948: 00d67663  bgeu         x12, x13, 0x00000954  # target 0x00000954
    94c: 0ff0000f  fence        0xf, 0xf
    950: fd5ff06f  jal          x0, 0x00000924  # target 0x00000924
loc_954:
    954: 0ff0000f  fence        0xf, 0xf
    958: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    95c: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    960: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898
    964: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    968: 00a484b3  add          x9, x9, x10
    96c: 000105b7  lui          x11, 0x00010  # x11 = 0x00010000
    970: fc058593  addi         x11, x11, -64  # x11 = 0x0000ffc0
    974: 00b4e663  bltu         x9, x11, 0x00000980  # target 0x00000980
    978: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    97c: 40c484b3  sub          x9, x9, x12
loc_980:
    980: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    984: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    988: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898; write runtime value
    98c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    990: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    994: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c
    998: 00248493  addi         x9, x9, 2
    99c: 01049493  slli         x9, x9, 16
    9a0: 0104d493  srli         x9, x9, 16
    9a4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    9a8: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    9ac: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c; write runtime value
    9b0: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    9b4: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    9b8: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    9bc: 0ff0000f  fence        0xf, 0xf
    9c0: 00125493  srli         x9, x4, 1
    9c4: 00949493  slli         x9, x9, 9
    9c8: 00139513  slli         x10, x7, 1
    9cc: 00a484b3  add          x9, x9, x10
    9d0: 240000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x000009d4
    9d4: 258000ef  jal          x1, 0x00000c2c  # target 0x00000c2c; x1 = 0x000009d8
    9d8: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    9dc: 8a480813  addi         x16, x16, -1884  # x16 = 0xffb008a4 · riscv_local_mem + 0x8a4
    9e0: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x8a4 · 0xffb008a4
loc_9e4:
    9e4: ffb49837  lui          x16, 0xffb49  # x16 = 0xffb49000
    9e8: 02080813  addi         x16, x16, 32  # x16 = 0xffb49020
    9ec: 00085603  lhu          x12, 0(x16)  # 0xffb49020
    9f0: 40c586b3  sub          x13, x11, x12
    9f4: 01069693  slli         x13, x13, 16
    9f8: 0106d693  srli         x13, x13, 16
    9fc: 00400713  addi         x14, x0, 4  # x14 = 0x00000004
    a00: 40d70733  sub          x14, x14, x13
    a04: 00200793  addi         x15, x0, 2  # x15 = 0x00000002
    a08: 00f77663  bgeu         x14, x15, 0x00000a14  # target 0x00000a14
    a0c: 0ff0000f  fence        0xf, 0xf
    a10: fd5ff06f  jal          x0, 0x000009e4  # target 0x000009e4
loc_a14:
    a14: 0ff0000f  fence        0xf, 0xf
    a18: 00048593  addi         x11, x9, 0
    a1c: 00058f93  addi         x31, x11, 0
    a20: 4b8000ef  jal          x1, 0x00000ed8  # target 0x00000ed8; x1 = 0x00000a24
    a24: 000a8613  addi         x12, x21, 0
    a28: 000b0693  addi         x13, x22, 0
    a2c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a30: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    a34: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    a38: 00060f93  addi         x31, x12, 0
    a3c: 00068f13  addi         x30, x13, 0
    a40: 00070e93  addi         x29, x14, 0
    a44: 250000ef  jal          x1, 0x00000c94  # target 0x00000c94; x1 = 0x00000a48
    a48: 00148593  addi         x11, x9, 1
    a4c: 00058f93  addi         x31, x11, 0
    a50: 488000ef  jal          x1, 0x00000ed8  # target 0x00000ed8; x1 = 0x00000a54
    a54: 000a8613  addi         x12, x21, 0
    a58: 000b0693  addi         x13, x22, 0
    a5c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a60: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    a64: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    a68: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a6c: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    a70: 00f70733  add          x14, x14, x15
    a74: 00060f93  addi         x31, x12, 0
    a78: 00068f13  addi         x30, x13, 0
    a7c: 00070e93  addi         x29, x14, 0
    a80: 214000ef  jal          x1, 0x00000c94  # target 0x00000c94; x1 = 0x00000a84
    a84: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    a88: 8ac80813  addi         x16, x16, -1876  # x16 = 0xffb008ac · riscv_local_mem + 0x8ac
    a8c: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x8ac · 0xffb008ac
loc_a90:
    a90: ffb4a837  lui          x16, 0xffb4a  # x16 = 0xffb4a000
    a94: 02080813  addi         x16, x16, 32  # x16 = 0xffb4a020
    a98: 00085603  lhu          x12, 0(x16)  # 0xffb4a020
    a9c: 40c586b3  sub          x13, x11, x12
    aa0: 01069693  slli         x13, x13, 16
    aa4: 0106d693  srli         x13, x13, 16
    aa8: 00400713  addi         x14, x0, 4  # x14 = 0x00000004
    aac: 40d70733  sub          x14, x14, x13
    ab0: 00200793  addi         x15, x0, 2  # x15 = 0x00000002
    ab4: 00f77663  bgeu         x14, x15, 0x00000ac0  # target 0x00000ac0
    ab8: 0ff0000f  fence        0xf, 0xf
    abc: fd5ff06f  jal          x0, 0x00000a90  # target 0x00000a90
loc_ac0:
    ac0: 0ff0000f  fence        0xf, 0xf
    ac4: 00048593  addi         x11, x9, 0
    ac8: 00058f93  addi         x31, x11, 0
    acc: 458000ef  jal          x1, 0x00000f24  # target 0x00000f24; x1 = 0x00000ad0
    ad0: 000a8613  addi         x12, x21, 0
    ad4: 000b0693  addi         x13, x22, 0
    ad8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    adc: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    ae0: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    ae4: 00060f93  addi         x31, x12, 0
    ae8: 00068f13  addi         x30, x13, 0
    aec: 00070e93  addi         x29, x14, 0
    af0: 1a4000ef  jal          x1, 0x00000c94  # target 0x00000c94; x1 = 0x00000af4
    af4: 00148593  addi         x11, x9, 1
    af8: 00058f93  addi         x31, x11, 0
    afc: 428000ef  jal          x1, 0x00000f24  # target 0x00000f24; x1 = 0x00000b00
    b00: 000a8613  addi         x12, x21, 0
    b04: 000b0693  addi         x13, x22, 0
    b08: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b0c: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    b10: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    b14: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    b18: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    b1c: 00f70733  add          x14, x14, x15
    b20: 00060f93  addi         x31, x12, 0
    b24: 00068f13  addi         x30, x13, 0
    b28: 00070e93  addi         x29, x14, 0
    b2c: 168000ef  jal          x1, 0x00000c94  # target 0x00000c94; x1 = 0x00000b30
    b30: 0fc000ef  jal          x1, 0x00000c2c  # target 0x00000c2c; x1 = 0x00000b34
    b34: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b38: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    b3c: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    b40: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    b44: 00c585b3  add          x11, x11, x12
    b48: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    b4c: fc068693  addi         x13, x13, -64  # x13 = 0x00011fc0
    b50: 00d5e663  bltu         x11, x13, 0x00000b5c  # target 0x00000b5c
    b54: 00002737  lui          x14, 0x00002  # x14 = 0x00002000
    b58: 40e585b3  sub          x11, x11, x14
loc_b5c:
    b5c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b60: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    b64: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0; write runtime value
    b68: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b6c: 8a460613  addi         x12, x12, -1884  # x12 = 0xffb008a4 · riscv_local_mem + 0x8a4
    b70: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x8a4 · 0xffb008a4
    b74: 00258593  addi         x11, x11, 2
    b78: 01059593  slli         x11, x11, 16
    b7c: 0105d593  srli         x11, x11, 16
    b80: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b84: 8a460613  addi         x12, x12, -1884  # x12 = 0xffb008a4 · riscv_local_mem + 0x8a4
    b88: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x8a4 · 0xffb008a4; write runtime value
    b8c: ffb49637  lui          x12, 0xffb49  # x12 = 0xffb49000
    b90: 02860613  addi         x12, x12, 40  # x12 = 0xffb49028
    b94: 00b62023  sw           x11, 0(x12)  # 0xffb49028; write runtime value
    b98: 0ff0000f  fence        0xf, 0xf
    b9c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    ba0: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    ba4: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    ba8: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    bac: 00c585b3  add          x11, x11, x12
    bb0: 000146b7  lui          x13, 0x00014  # x13 = 0x00014000
    bb4: fc068693  addi         x13, x13, -64  # x13 = 0x00013fc0
    bb8: 00d5e663  bltu         x11, x13, 0x00000bc4  # target 0x00000bc4
    bbc: 00002737  lui          x14, 0x00002  # x14 = 0x00002000
    bc0: 40e585b3  sub          x11, x11, x14
loc_bc4:
    bc4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    bc8: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    bcc: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8; write runtime value
    bd0: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    bd4: 8ac60613  addi         x12, x12, -1876  # x12 = 0xffb008ac · riscv_local_mem + 0x8ac
    bd8: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x8ac · 0xffb008ac
    bdc: 00258593  addi         x11, x11, 2
    be0: 01059593  slli         x11, x11, 16
    be4: 0105d593  srli         x11, x11, 16
    be8: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    bec: 8ac60613  addi         x12, x12, -1876  # x12 = 0xffb008ac · riscv_local_mem + 0x8ac
    bf0: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x8ac · 0xffb008ac; write runtime value
    bf4: ffb4a637  lui          x12, 0xffb4a  # x12 = 0xffb4a000
    bf8: 02860613  addi         x12, x12, 40  # x12 = 0xffb4a028
    bfc: 00b62023  sw           x11, 0(x12)  # 0xffb4a028; write runtime value
    c00: 0ff0000f  fence        0xf, 0xf
    c04: 00138393  addi         x7, x7, 1
    c08: d0dff06f  jal          x0, 0x00000914  # target 0x00000914
loc_c0c:
    c0c: 3640006f  jal          x0, 0x00000f70  # target 0x00000f70
loc_c10:
    c10: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c14: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    c18: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    c1c: 000a0463  beq          x20, x0, 0x00000c24  # target 0x00000c24
    c20: ff1ff06f  jal          x0, 0x00000c10  # target 0x00000c10
loc_c24:
    c24: 0ff0000f  fence        0xf, 0xf
    c28: 00008067  jalr         x0, 0(x1)
loc_c2c:
    c2c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c30: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    c34: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    c38: 000a0463  beq          x20, x0, 0x00000c40  # target 0x00000c40
    c3c: ff1ff06f  jal          x0, 0x00000c2c  # target 0x00000c2c
loc_c40:
    c40: 0ff0000f  fence        0xf, 0xf
    c44: 00008067  jalr         x0, 0(x1)
loc_c48:
    c48: 7a400a93  addi         x21, x0, 1956  # x21 = 0x000007a4
    c4c: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_cos; 0x000007a4
    c50: 007a7d13  andi         x26, x20, 7
    c54: ff8a7a13  andi         x20, x20, -8
    c58: 01af8ab3  add          x21, x31, x26
    c5c: 007afb93  andi         x23, x21, 7
    c60: 003ada93  srli         x21, x21, 3
    c64: 00ba9a93  slli         x21, x21, 11
    c68: 014a8ab3  add          x21, x21, x20
    c6c: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000c6c
    c70: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000c84
    c74: 001b9b93  slli         x23, x23, 1
    c78: 017b0b33  add          x22, x22, x23
    c7c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    c80: 00008067  jalr         x0, 0(x1)
    c84: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    c88: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    c8c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    c90: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_c94:
    c94: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c98: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    c9c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    ca0: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    ca4: 015a6463  bltu         x20, x21, 0x00000cac  # target 0x00000cac
    ca8: fedff06f  jal          x0, 0x00000c94  # target 0x00000c94
loc_cac:
    cac: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    cb0: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    cb4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    cb8: 014a1a13  slli         x20, x20, 20
    cbc: 014a5a13  srli         x20, x20, 20
    cc0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_cc4:
    cc4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    cc8: 000b0463  beq          x22, x0, 0x00000cd0  # target 0x00000cd0
    ccc: ff9ff06f  jal          x0, 0x00000cc4  # target 0x00000cc4
loc_cd0:
    cd0: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    cd4: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    cd8: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    cdc: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    ce0: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    ce4: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    ce8: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    cec: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    cf0: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    cf4: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    cf8: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    cfc: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    d00: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    d04: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    d08: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    d0c: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    d10: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    d14: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    d18: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    d1c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    d20: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    d24: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_d28:
    d28: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    d2c: 000b0463  beq          x22, x0, 0x00000d34  # target 0x00000d34
    d30: ff9ff06f  jal          x0, 0x00000d28  # target 0x00000d28
loc_d34:
    d34: 00008067  jalr         x0, 0(x1)
loc_d38:
    d38: 7a800a93  addi         x21, x0, 1960  # x21 = 0x000007a8
    d3c: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_sin; 0x000007a8
    d40: 007a7d13  andi         x26, x20, 7
    d44: ff8a7a13  andi         x20, x20, -8
    d48: 01af8ab3  add          x21, x31, x26
    d4c: 007afb93  andi         x23, x21, 7
    d50: 003ada93  srli         x21, x21, 3
    d54: 00ba9a93  slli         x21, x21, 11
    d58: 014a8ab3  add          x21, x21, x20
    d5c: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d5c
    d60: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d74
    d64: 001b9b93  slli         x23, x23, 1
    d68: 017b0b33  add          x22, x22, x23
    d6c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d70: 00008067  jalr         x0, 0(x1)
    d74: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    d78: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d7c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    d80: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d84:
    d84: 79800a93  addi         x21, x0, 1944  # x21 = 0x00000798
    d88: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_q_compact; 0x00000798
    d8c: 007a7d13  andi         x26, x20, 7
    d90: ff8a7a13  andi         x20, x20, -8
    d94: 01af8ab3  add          x21, x31, x26
    d98: 007afb93  andi         x23, x21, 7
    d9c: 003ada93  srli         x21, x21, 3
    da0: 00ba9a93  slli         x21, x21, 11
    da4: 014a8ab3  add          x21, x21, x20
    da8: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000da8
    dac: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000dc0
    db0: 001b9b93  slli         x23, x23, 1
    db4: 017b0b33  add          x22, x22, x23
    db8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    dbc: 00008067  jalr         x0, 0(x1)
    dc0: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    dc4: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    dc8: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    dcc: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_dd0:
    dd0: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    dd4: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_k_compact; 0x0000079c
    dd8: 007a7d13  andi         x26, x20, 7
    ddc: ff8a7a13  andi         x20, x20, -8
    de0: 01af8ab3  add          x21, x31, x26
    de4: 007afb93  andi         x23, x21, 7
    de8: 003ada93  srli         x21, x21, 3
    dec: 00ba9a93  slli         x21, x21, 11
    df0: 014a8ab3  add          x21, x21, x20
    df4: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000df4
    df8: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e0c
    dfc: 001b9b93  slli         x23, x23, 1
    e00: 017b0b33  add          x22, x22, x23
    e04: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e08: 00008067  jalr         x0, 0(x1)
    e0c: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    e10: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e14: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    e18: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_e1c:
    e1c: 7a000a93  addi         x21, x0, 1952  # x21 = 0x000007a0
    e20: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_v_compact; 0x000007a0
    e24: 007a7d13  andi         x26, x20, 7
    e28: ff8a7a13  andi         x20, x20, -8
    e2c: 01af8ab3  add          x21, x31, x26
    e30: 007afb93  andi         x23, x21, 7
    e34: 003ada93  srli         x21, x21, 3
    e38: 00ba9a93  slli         x21, x21, 11
    e3c: 014a8ab3  add          x21, x21, x20
    e40: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e40
    e44: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e58
    e48: 001b9b93  slli         x23, x23, 1
    e4c: 017b0b33  add          x22, x22, x23
    e50: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e54: 00008067  jalr         x0, 0(x1)
    e58: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    e5c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e60: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    e64: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_e68:
    e68: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    e6c: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    e70: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    e74: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    e78: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    e7c: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    e80: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    e84: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    e88: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    e8c: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    e90: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    e94: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    e98: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    e9c: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    ea0: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    ea4: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    ea8: 020f8f93  addi         x31, x31, 32
    eac: 020f0f13  addi         x30, x30, 32
    eb0: ff8e8e93  addi         x29, x29, -8
    eb4: fa0e9ae3  bne          x29, x0, 0x00000e68  # target 0x00000e68
    eb8: 00008067  jalr         x0, 0(x1)
loc_ebc:
    ebc: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    ec0: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    ec4: 004f8f93  addi         x31, x31, 4
    ec8: 004f0f13  addi         x30, x30, 4
    ecc: fffe8e93  addi         x29, x29, -1
    ed0: fe0e96e3  bne          x29, x0, 0x00000ebc  # target 0x00000ebc
    ed4: 00008067  jalr         x0, 0(x1)
loc_ed8:
    ed8: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    edc: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    ee0: 007a7d13  andi         x26, x20, 7
    ee4: ff8a7a13  andi         x20, x20, -8
    ee8: 01af8ab3  add          x21, x31, x26
    eec: 007afb93  andi         x23, x21, 7
    ef0: 003ada93  srli         x21, x21, 3
    ef4: 00ba9a93  slli         x21, x21, 11
    ef8: 014a8ab3  add          x21, x21, x20
    efc: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000efc
    f00: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000f14
    f04: 001b9b93  slli         x23, x23, 1
    f08: 017b0b33  add          x22, x22, x23
    f0c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    f10: 00008067  jalr         x0, 0(x1)
    f14: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    f18: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    f1c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    f20: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_f24:
    f24: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    f28: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    f2c: 007a7d13  andi         x26, x20, 7
    f30: ff8a7a13  andi         x20, x20, -8
    f34: 01af8ab3  add          x21, x31, x26
    f38: 007afb93  andi         x23, x21, 7
    f3c: 003ada93  srli         x21, x21, 3
    f40: 00ba9a93  slli         x21, x21, 11
    f44: 014a8ab3  add          x21, x21, x20
    f48: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000f48
    f4c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000f60
    f50: 001b9b93  slli         x23, x23, 1
    f54: 017b0b33  add          x22, x22, x23
    f58: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    f5c: 00008067  jalr         x0, 0(x1)
    f60: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    f64: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    f68: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    f6c: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    f70:           j FW_BRISC+4   # return to firmware, linked at install
