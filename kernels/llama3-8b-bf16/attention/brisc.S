# llama3 8b-bf16 decode: attention, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (32): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=attention_core
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 0001f2b7  lui          x5, 0x0001f  # x5 = 0x0001f000
      c: fc028293  addi         x5, x5, -64  # x5 = 0x0001efc0
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0001efc0
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     28: 000212b7  lui          x5, 0x00021  # x5 = 0x00021000
     2c: 7c028293  addi         x5, x5, 1984  # x5 = 0x000217c0
     30: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x000217c0
     34: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     38: 88420213  addi         x4, x4, -1916  # x4 = 0xffb00884 · riscv_local_mem + 0x884
     3c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     40: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     44: 88838393  addi         x7, x7, -1912  # x7 = 0xffb00888 · riscv_local_mem + 0x888
     48: 0001c437  lui          x8, 0x0001c  # x8 = 0x0001c000
     4c: fc040413  addi         x8, x8, -64  # x8 = 0x0001bfc0
     50: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x888 · 0xffb00888; write 0x0001bfc0
     54: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     58: 88c38393  addi         x7, x7, -1908  # x7 = 0xffb0088c · riscv_local_mem + 0x88c
     5c: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x88c · 0xffb0088c; write 0x00000000
     60: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     64: 89038393  addi         x7, x7, -1904  # x7 = 0xffb00890 · riscv_local_mem + 0x890
     68: 0001b437  lui          x8, 0x0001b  # x8 = 0x0001b000
     6c: fc040413  addi         x8, x8, -64  # x8 = 0x0001afc0
     70: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x890 · 0xffb00890; write 0x0001afc0
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
     a8: 00011637  lui          x12, 0x00011  # x12 = 0x00011000
     ac: fc060613  addi         x12, x12, -64  # x12 = 0x00010fc0
     b0: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x8a0 · 0xffb008a0; write 0x00010fc0
     b4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     b8: 8a458593  addi         x11, x11, -1884  # x11 = 0xffb008a4 · riscv_local_mem + 0x8a4
     bc: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x8a4 · 0xffb008a4; write 0x00000000
     c0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     c4: 8a858593  addi         x11, x11, -1880  # x11 = 0xffb008a8 · riscv_local_mem + 0x8a8
     c8: 00015637  lui          x12, 0x00015  # x12 = 0x00015000
     cc: fc060613  addi         x12, x12, -64  # x12 = 0x00014fc0
     d0: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x8a8 · 0xffb008a8; write 0x00014fc0
     d4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     d8: 8ac58593  addi         x11, x11, -1876  # x11 = 0xffb008ac · riscv_local_mem + 0x8ac
     dc: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x8ac · 0xffb008ac; write 0x00000000
     e0: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
     e4: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
     e8: 00325293  srli         x5, x4, 3
     ec: 00727313  andi         x6, x4, 7
     f0: 00731313  slli         x6, x6, 7
     f4: 00131313  slli         x6, x6, 1
     f8: 3cd000ef  jal          x1, 0x00000cc4  # target 0x00000cc4; x1 = 0x000000fc
     fc: 3e5000ef  jal          x1, 0x00000ce0  # target 0x00000ce0; x1 = 0x00000100
    100: 00028f93  addi         x31, x5, 0
    104: 3f9000ef  jal          x1, 0x00000cfc  # target 0x00000cfc; x1 = 0x00000108
    108: 000a8393  addi         x7, x21, 0
    10c: 000b0413  addi         x8, x22, 0
    110: 00038f93  addi         x31, x7, 0
    114: 00040f13  addi         x30, x8, 0
    118: 00036eb7  lui          x29, 0x00036  # x29 = 0x00036000 · arc_apb_reset_unit + 0x6000
    11c: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000367c0 · arc_apb_reset_unit + 0x67c0
    120: 429000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000124
    124: 00028f93  addi         x31, x5, 0
    128: 4c5000ef  jal          x1, 0x00000dec  # target 0x00000dec; x1 = 0x0000012c
    12c: 000a8393  addi         x7, x21, 0
    130: 000b0413  addi         x8, x22, 0
    134: 00038f93  addi         x31, x7, 0
    138: 00040f13  addi         x30, x8, 0
    13c: 00037eb7  lui          x29, 0x00037  # x29 = 0x00037000 · arc_apb_reset_unit + 0x7000
    140: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00036fc0 · arc_apb_reset_unit + 0x6fc0
    144: 405000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000148
    148: 399000ef  jal          x1, 0x00000ce0  # target 0x00000ce0; x1 = 0x0000014c
    14c: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    150: 90048493  addi         x9, x9, -1792  # x9 = 0x0000e900
    154: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x0000e900
    158: 00741413  slli         x8, x8, 7
    15c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
loc_160:
    160: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    164: 8d068693  addi         x13, x13, -1840  # x13 = 0x000008d0
    168: 00d47c63  bgeu         x8, x13, 0x00000180  # target 0x00000180
    16c: 02f00613  addi         x12, x0, 47  # x12 = 0x0000002f
    170: 02c454b3  divu         x9, x8, x12
    174: 02c485b3  mul          x11, x9, x12
    178: 40b405b3  sub          x11, x8, x11
    17c: 01c0006f  jal          x0, 0x00000198  # target 0x00000198
loc_180:
    180: 40d406b3  sub          x13, x8, x13
    184: 02e00613  addi         x12, x0, 46  # x12 = 0x0000002e
    188: 02c6d4b3  divu         x9, x13, x12
    18c: 02c485b3  mul          x11, x9, x12
    190: 40b685b3  sub          x11, x13, x11
    194: 03048493  addi         x9, x9, 48
loc_198:
    198: 07f40513  addi         x10, x8, 127
    19c: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1a0: 8d078793  addi         x15, x15, -1840  # x15 = 0x000008d0
    1a4: 00f57c63  bgeu         x10, x15, 0x000001bc  # target 0x000001bc
    1a8: 02f00713  addi         x14, x0, 47  # x14 = 0x0000002f
    1ac: 02e55633  divu         x12, x10, x14
    1b0: 02e606b3  mul          x13, x12, x14
    1b4: 40d506b3  sub          x13, x10, x13
    1b8: 01c0006f  jal          x0, 0x000001d4  # target 0x000001d4
loc_1bc:
    1bc: 40f507b3  sub          x15, x10, x15
    1c0: 02e00713  addi         x14, x0, 46  # x14 = 0x0000002e
    1c4: 02e7d633  divu         x12, x15, x14
    1c8: 02e606b3  mul          x13, x12, x14
    1cc: 40d786b3  sub          x13, x15, x13
    1d0: 03060613  addi         x12, x12, 48
loc_1d4:
    1d4: 00048513  addi         x10, x9, 0
    1d8: 2ed000ef  jal          x1, 0x00000cc4  # target 0x00000cc4; x1 = 0x000001dc
    1dc: 305000ef  jal          x1, 0x00000ce0  # target 0x00000ce0; x1 = 0x000001e0
    1e0: 00022737  lui          x14, 0x00022  # x14 = 0x00022000
    1e4: fc070713  addi         x14, x14, -64  # x14 = 0x00021fc0
loc_1e8:
    1e8: 00050f93  addi         x31, x10, 0
    1ec: 44d000ef  jal          x1, 0x00000e38  # target 0x00000e38; x1 = 0x000001f0
    1f0: 000a8793  addi         x15, x21, 0
    1f4: 000b0813  addi         x16, x22, 0
    1f8: 00078f93  addi         x31, x15, 0
    1fc: 00080f13  addi         x30, x16, 0
    200: 00070e93  addi         x29, x14, 0
    204: 345000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000208
    208: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    20c: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    210: 00f70733  add          x14, x14, x15
    214: 00150513  addi         x10, x10, 1
    218: fca678e3  bgeu         x12, x10, 0x000001e8  # target 0x000001e8
    21c: 2c5000ef  jal          x1, 0x00000ce0  # target 0x00000ce0; x1 = 0x00000220
    220: 00048513  addi         x10, x9, 0
    224: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    228: 00839693  slli         x13, x7, 8
    22c: 0001f737  lui          x14, 0x0001f  # x14 = 0x0001f000
    230: fc070713  addi         x14, x14, -64  # x14 = 0x0001efc0
    234: 00e686b3  add          x13, x13, x14
loc_238:
    238: 02e00713  addi         x14, x0, 46  # x14 = 0x0000002e
    23c: 03000793  addi         x15, x0, 48  # x15 = 0x00000030
    240: 00f57463  bgeu         x10, x15, 0x00000248  # target 0x00000248
    244: 00170713  addi         x14, x14, 1  # x14 = 0x0000002f
loc_248:
    248: 40b70733  sub          x14, x14, x11
    24c: 00f5f793  andi         x15, x11, 15
    250: 40f007b3  sub          x15, x0, x15
    254: 01078793  addi         x15, x15, 16
    258: 00e7f463  bgeu         x15, x14, 0x00000260  # target 0x00000260
    25c: 00078713  addi         x14, x15, 0
loc_260:
    260: 03f67793  andi         x15, x12, 63
    264: 40f007b3  sub          x15, x0, x15
    268: 04078793  addi         x15, x15, 64
    26c: 00e7f463  bgeu         x15, x14, 0x00000274  # target 0x00000274
    270: 00078713  addi         x14, x15, 0
loc_274:
    274: 40950833  sub          x16, x10, x9
    278: 00b81813  slli         x16, x16, 11
    27c: 00f5f793  andi         x15, x11, 15
    280: 00179793  slli         x15, x15, 1
    284: 0105fa13  andi         x20, x11, 16
    288: 005a1a13  slli         x20, x20, 5
    28c: 0147e7b3  or           x15, x15, x20
    290: 1e05fa13  andi         x20, x11, 480
    294: 0147e7b3  or           x15, x15, x20
    298: 0095da13  srli         x20, x11, 9
    29c: 00aa1a13  slli         x20, x20, 10
    2a0: 0147e7b3  or           x15, x15, x20
    2a4: 00f80833  add          x16, x16, x15
    2a8: 00022a37  lui          x20, 0x00022  # x20 = 0x00022000
    2ac: fc0a0a13  addi         x20, x20, -64  # x20 = 0x00021fc0
    2b0: 01480833  add          x16, x16, x20
    2b4: 00161893  slli         x17, x12, 1
    2b8: 00d888b3  add          x17, x17, x13
    2bc: 04064913  xori         x18, x12, 64
    2c0: 00191913  slli         x18, x18, 1
    2c4: 00d90933  add          x18, x18, x13
    2c8: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2cc: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    2d0: 01490933  add          x18, x18, x20
    2d4: 04067993  andi         x19, x12, 64
    2d8: 00999993  slli         x19, x19, 9
    2dc: 00080f93  addi         x31, x16, 0
    2e0: 00088f13  addi         x30, x17, 0
    2e4: 00090e93  addi         x29, x18, 0
    2e8: 00070e13  addi         x28, x14, 0
    2ec: 00098d93  addi         x27, x19, 0
loc_2f0:
    2f0: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    2f4: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    2f8: 01ba4a33  xor          x20, x20, x27
    2fc: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    300: 002f8f93  addi         x31, x31, 2
    304: 002f0f13  addi         x30, x30, 2
    308: 002e8e93  addi         x29, x29, 2
    30c: fffe0e13  addi         x28, x28, -1
    310: fe0e10e3  bne          x28, x0, 0x000002f0  # target 0x000002f0
    314: 00e60633  add          x12, x12, x14
    318: 00e585b3  add          x11, x11, x14
    31c: 02e00793  addi         x15, x0, 46  # x15 = 0x0000002e
    320: 03000993  addi         x19, x0, 48  # x19 = 0x00000030
    324: 01357463  bgeu         x10, x19, 0x0000032c  # target 0x0000032c
    328: 00178793  addi         x15, x15, 1  # x15 = 0x0000002f
loc_32c:
    32c: 00f59663  bne          x11, x15, 0x00000338  # target 0x00000338
    330: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    334: 00150513  addi         x10, x10, 1
loc_338:
    338: 08000793  addi         x15, x0, 128  # x15 = 0x00000080
    33c: eef66ee3  bltu         x12, x15, 0x00000238  # target 0x00000238
    340: 08040413  addi         x8, x8, 128
    344: 00138393  addi         x7, x7, 1
    348: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
    34c: e0939ae3  bne          x7, x9, 0x00000160  # target 0x00000160
    350: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    354: 90048493  addi         x9, x9, -1792  # x9 = 0x0000e900
    358: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x0000e900
    35c: 00245413  srli         x8, x8, 2
    360: 00741413  slli         x8, x8, 7
    364: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
    368: 2a000693  addi         x13, x0, 672  # x13 = 0x000002a0
    36c: 00d47c63  bgeu         x8, x13, 0x00000384  # target 0x00000384
    370: 00c00613  addi         x12, x0, 12  # x12 = 0x0000000c
    374: 02c454b3  divu         x9, x8, x12
    378: 02c485b3  mul          x11, x9, x12
    37c: 40b405b3  sub          x11, x8, x11
    380: 01c0006f  jal          x0, 0x0000039c  # target 0x0000039c
loc_384:
    384: 40d406b3  sub          x13, x8, x13
    388: 00b00613  addi         x12, x0, 11  # x12 = 0x0000000b
    38c: 02c6d4b3  divu         x9, x13, x12
    390: 02c485b3  mul          x11, x9, x12
    394: 40b685b3  sub          x11, x13, x11
    398: 03848493  addi         x9, x9, 56
loc_39c:
    39c: 07f40513  addi         x10, x8, 127
    3a0: 2a000793  addi         x15, x0, 672  # x15 = 0x000002a0
    3a4: 00f57c63  bgeu         x10, x15, 0x000003bc  # target 0x000003bc
    3a8: 00c00713  addi         x14, x0, 12  # x14 = 0x0000000c
    3ac: 02e55633  divu         x12, x10, x14
    3b0: 02e606b3  mul          x13, x12, x14
    3b4: 40d506b3  sub          x13, x10, x13
    3b8: 01c0006f  jal          x0, 0x000003d4  # target 0x000003d4
loc_3bc:
    3bc: 40f507b3  sub          x15, x10, x15
    3c0: 00b00713  addi         x14, x0, 11  # x14 = 0x0000000b
    3c4: 02e7d633  divu         x12, x15, x14
    3c8: 02e606b3  mul          x13, x12, x14
    3cc: 40d786b3  sub          x13, x15, x13
    3d0: 03860613  addi         x12, x12, 56
loc_3d4:
    3d4: 00048513  addi         x10, x9, 0
    3d8: 0ed000ef  jal          x1, 0x00000cc4  # target 0x00000cc4; x1 = 0x000003dc
    3dc: 105000ef  jal          x1, 0x00000ce0  # target 0x00000ce0; x1 = 0x000003e0
    3e0: 00022737  lui          x14, 0x00022  # x14 = 0x00022000
    3e4: fc070713  addi         x14, x14, -64  # x14 = 0x00021fc0
loc_3e8:
    3e8: 00050f93  addi         x31, x10, 0
    3ec: 299000ef  jal          x1, 0x00000e84  # target 0x00000e84; x1 = 0x000003f0
    3f0: 000a8793  addi         x15, x21, 0
    3f4: 000b0813  addi         x16, x22, 0
    3f8: 00078f93  addi         x31, x15, 0
    3fc: 00080f13  addi         x30, x16, 0
    400: 00070e93  addi         x29, x14, 0
    404: 145000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000408
    408: 00050f93  addi         x31, x10, 0
    40c: 2c5000ef  jal          x1, 0x00000ed0  # target 0x00000ed0; x1 = 0x00000410
    410: 000a8793  addi         x15, x21, 0
    414: 000b0813  addi         x16, x22, 0
    418: 0000a8b7  lui          x17, 0x0000a  # x17 = 0x0000a000
    41c: 00e888b3  add          x17, x17, x14
    420: 00078f93  addi         x31, x15, 0
    424: 00080f13  addi         x30, x16, 0
    428: 00088e93  addi         x29, x17, 0
    42c: 11d000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000430
    430: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    434: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    438: 00f70733  add          x14, x14, x15
    43c: 00150513  addi         x10, x10, 1
    440: faa674e3  bgeu         x12, x10, 0x000003e8  # target 0x000003e8
    444: 09d000ef  jal          x1, 0x00000ce0  # target 0x00000ce0; x1 = 0x00000448
    448: 00048513  addi         x10, x9, 0
    44c: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    450: 00839693  slli         x13, x7, 8
    454: 0001f737  lui          x14, 0x0001f  # x14 = 0x0001f000
    458: fc070713  addi         x14, x14, -64  # x14 = 0x0001efc0
    45c: 00e686b3  add          x13, x13, x14
loc_460:
    460: 00b00713  addi         x14, x0, 11  # x14 = 0x0000000b
    464: 03800793  addi         x15, x0, 56  # x15 = 0x00000038
    468: 00f57463  bgeu         x10, x15, 0x00000470  # target 0x00000470
    46c: 00170713  addi         x14, x14, 1  # x14 = 0x0000000c
loc_470:
    470: 40b70733  sub          x14, x14, x11
    474: 00f5f793  andi         x15, x11, 15
    478: 40f007b3  sub          x15, x0, x15
    47c: 01078793  addi         x15, x15, 16
    480: 00e7f463  bgeu         x15, x14, 0x00000488  # target 0x00000488
    484: 00078713  addi         x14, x15, 0
loc_488:
    488: 03f67793  andi         x15, x12, 63
    48c: 40f007b3  sub          x15, x0, x15
    490: 04078793  addi         x15, x15, 64
    494: 00e7f463  bgeu         x15, x14, 0x0000049c  # target 0x0000049c
    498: 00078713  addi         x14, x15, 0
loc_49c:
    49c: 40950833  sub          x16, x10, x9
    4a0: 00b81813  slli         x16, x16, 11
    4a4: 00f5f793  andi         x15, x11, 15
    4a8: 00179793  slli         x15, x15, 1
    4ac: 0105fa13  andi         x20, x11, 16
    4b0: 005a1a13  slli         x20, x20, 5
    4b4: 0147e7b3  or           x15, x15, x20
    4b8: 1e05fa13  andi         x20, x11, 480
    4bc: 0147e7b3  or           x15, x15, x20
    4c0: 0095da13  srli         x20, x11, 9
    4c4: 00aa1a13  slli         x20, x20, 10
    4c8: 0147e7b3  or           x15, x15, x20
    4cc: 00f80833  add          x16, x16, x15
    4d0: 00022a37  lui          x20, 0x00022  # x20 = 0x00022000
    4d4: fc0a0a13  addi         x20, x20, -64  # x20 = 0x00021fc0
    4d8: 01480833  add          x16, x16, x20
    4dc: 00161893  slli         x17, x12, 1
    4e0: 00d888b3  add          x17, x17, x13
    4e4: 04064913  xori         x18, x12, 64
    4e8: 00191913  slli         x18, x18, 1
    4ec: 00d90933  add          x18, x18, x13
    4f0: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4f4: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    4f8: 01490933  add          x18, x18, x20
    4fc: 04067993  andi         x19, x12, 64
    500: 00999993  slli         x19, x19, 9
    504: 0000aa37  lui          x20, 0x0000a  # x20 = 0x0000a000
    508: 010a0a33  add          x20, x20, x16
    50c: 00161a93  slli         x21, x12, 1
    510: 00036b37  lui          x22, 0x00036  # x22 = 0x00036000 · arc_apb_reset_unit + 0x6000
    514: fc0b0b13  addi         x22, x22, -64  # x22 = 0x00035fc0 · arc_apb_reset_unit + 0x5fc0
    518: 016a8ab3  add          x21, x21, x22
    51c: ffc10113  addi         x2, x2, -4
    520: 01412023  sw           x20, 0(x2)  # Address depends on runtime register values
    524: 00080f93  addi         x31, x16, 0
    528: 00088f13  addi         x30, x17, 0
    52c: 00090e93  addi         x29, x18, 0
    530: 00070e13  addi         x28, x14, 0
    534: 00098d93  addi         x27, x19, 0
    538: 000a0d13  addi         x26, x20, 0
    53c: 000a8c93  addi         x25, x21, 0
loc_540:
    540: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    544: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    548: 01ba4a33  xor          x20, x20, x27
    54c: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    550: 000d5a03  lhu          x20, 0(x26)  # Address depends on runtime register values
    554: 014c9023  sh           x20, 0(x25)  # Address depends on runtime register values
    558: 002d0d13  addi         x26, x26, 2
    55c: 002c8c93  addi         x25, x25, 2
    560: 002f8f93  addi         x31, x31, 2
    564: 002f0f13  addi         x30, x30, 2
    568: 002e8e93  addi         x29, x29, 2
    56c: fffe0e13  addi         x28, x28, -1
    570: fc0e18e3  bne          x28, x0, 0x00000540  # target 0x00000540
    574: 00012a03  lw           x20, 0(x2)  # Address depends on runtime register values
    578: 00410113  addi         x2, x2, 4
    57c: 00e60633  add          x12, x12, x14
    580: 00e585b3  add          x11, x11, x14
    584: 00b00793  addi         x15, x0, 11  # x15 = 0x0000000b
    588: 03800993  addi         x19, x0, 56  # x19 = 0x00000038
    58c: 01357463  bgeu         x10, x19, 0x00000594  # target 0x00000594
    590: 00178793  addi         x15, x15, 1  # x15 = 0x0000000c
loc_594:
    594: 00f59663  bne          x11, x15, 0x000005a0  # target 0x000005a0
    598: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    59c: 00150513  addi         x10, x10, 1
loc_5a0:
    5a0: 08000793  addi         x15, x0, 128  # x15 = 0x00000080
    5a4: eaf66ee3  bltu         x12, x15, 0x00000460  # target 0x00000460
    5a8: 000363b7  lui          x7, 0x00036  # x7 = 0x00036000 · arc_apb_reset_unit + 0x6000
    5ac: 7c038393  addi         x7, x7, 1984  # x7 = 0x000367c0 · arc_apb_reset_unit + 0x67c0
    5b0: 006383b3  add          x7, x7, x6
    5b4: 00038f93  addi         x31, x7, 0
    5b8: 00020f37  lui          x30, 0x00020  # x30 = 0x00020000
    5bc: fc0f0f13  addi         x30, x30, -64  # x30 = 0x0001ffc0
    5c0: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5c4: 159000ef  jal          x1, 0x00000f1c  # target 0x00000f1c; x1 = 0x000005c8
    5c8: 00020fb7  lui          x31, 0x00020  # x31 = 0x00020000
    5cc: fc0f8f93  addi         x31, x31, -64  # x31 = 0x0001ffc0
    5d0: 00020f37  lui          x30, 0x00020  # x30 = 0x00020000
    5d4: 0c0f0f13  addi         x30, x30, 192  # x30 = 0x000200c0
    5d8: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5dc: 195000ef  jal          x1, 0x00000f70  # target 0x00000f70; x1 = 0x000005e0
    5e0: 000373b7  lui          x7, 0x00037  # x7 = 0x00037000 · arc_apb_reset_unit + 0x7000
    5e4: fc038393  addi         x7, x7, -64  # x7 = 0x00036fc0 · arc_apb_reset_unit + 0x6fc0
    5e8: 006383b3  add          x7, x7, x6
    5ec: 00038f93  addi         x31, x7, 0
    5f0: 00020f37  lui          x30, 0x00020  # x30 = 0x00020000
    5f4: 7c0f0f13  addi         x30, x30, 1984  # x30 = 0x000207c0
    5f8: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5fc: 121000ef  jal          x1, 0x00000f1c  # target 0x00000f1c; x1 = 0x00000600
    600: 00020fb7  lui          x31, 0x00020  # x31 = 0x00020000
    604: 7c0f8f93  addi         x31, x31, 1984  # x31 = 0x000207c0
    608: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    60c: 8c0f0f13  addi         x30, x30, -1856  # x30 = 0x000208c0
    610: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    614: 15d000ef  jal          x1, 0x00000f70  # target 0x00000f70; x1 = 0x00000618
    618: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    61c: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    620: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    624: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    628: 00520233  add          x4, x4, x5
    62c: 00021337  lui          x6, 0x00021  # x6 = 0x00021000
    630: fc030313  addi         x6, x6, -64  # x6 = 0x00020fc0
    634: 00626663  bltu         x4, x6, 0x00000640  # target 0x00000640
    638: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    63c: 40720233  sub          x4, x4, x7
loc_640:
    640: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    644: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    648: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    64c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    650: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    654: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    658: 00420213  addi         x4, x4, 4
    65c: 01021213  slli         x4, x4, 16
    660: 01025213  srli         x4, x4, 16
    664: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    668: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    66c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    670: ffb4f2b7  lui          x5, 0xffb4f  # x5 = 0xffb4f000
    674: 02828293  addi         x5, x5, 40  # x5 = 0xffb4f028
    678: 0042a023  sw           x4, 0(x5)  # 0xffb4f028; write runtime value
    67c: 0ff0000f  fence        0xf, 0xf
    680: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    684: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
    688: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884
    68c: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_690:
    690: ffb51437  lui          x8, 0xffb51  # x8 = 0xffb51000
    694: 02840413  addi         x8, x8, 40  # x8 = 0xffb51028
    698: 00045283  lhu          x5, 0(x8)  # 0xffb51028
    69c: 40428333  sub          x6, x5, x4
    6a0: 01031313  slli         x6, x6, 16
    6a4: 01035313  srli         x6, x6, 16
    6a8: 00737663  bgeu         x6, x7, 0x000006b4  # target 0x000006b4
    6ac: 0ff0000f  fence        0xf, 0xf
    6b0: fe1ff06f  jal          x0, 0x00000690  # target 0x00000690
loc_6b4:
    6b4: 0ff0000f  fence        0xf, 0xf
    6b8: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
    6bc: 90038393  addi         x7, x7, -1792  # x7 = 0x0000e900
    6c0: 0003a203  lw           x4, 0(x7)  # param attention_core; 0x0000e900
    6c4: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    6c8: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000790
    6cc: 79400393  addi         x7, x0, 1940  # x7 = 0x00000794
    6d0: 0003a303  lw           x6, 0(x7)  # param valid_columns; 0x00000794
    6d4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    6d8: 88c60613  addi         x12, x12, -1908  # x12 = 0xffb0088c · riscv_local_mem + 0x88c
    6dc: 00062383  lw           x7, 0(x12)  # riscv_local_mem + 0x88c · 0xffb0088c
loc_6e0:
    6e0: ffb4d637  lui          x12, 0xffb4d  # x12 = 0xffb4d000
    6e4: 02060613  addi         x12, x12, 32  # x12 = 0xffb4d020
    6e8: 00065403  lhu          x8, 0(x12)  # 0xffb4d020
    6ec: 408384b3  sub          x9, x7, x8
    6f0: 01049493  slli         x9, x9, 16
    6f4: 0104d493  srli         x9, x9, 16
    6f8: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
    6fc: 40950533  sub          x10, x10, x9
    700: 00100593  addi         x11, x0, 1  # x11 = 0x00000001
    704: 00b57663  bgeu         x10, x11, 0x00000710  # target 0x00000710
    708: 0ff0000f  fence        0xf, 0xf
    70c: fd5ff06f  jal          x0, 0x000006e0  # target 0x000006e0
loc_710:
    710: 0ff0000f  fence        0xf, 0xf
    714: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    718: 88840413  addi         x8, x8, -1912  # x8 = 0xffb00888 · riscv_local_mem + 0x888
    71c: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x888 · 0xffb00888
    720: 00038413  addi         x8, x7, 0
    724: 40000493  addi         x9, x0, 1024  # x9 = 0x00000400
loc_728:
    728: 00042023  sw           x0, 0(x8)  # Address depends on runtime register values
    72c: 00042223  sw           x0, 4(x8)  # Address depends on runtime register values
    730: 00042423  sw           x0, 8(x8)  # Address depends on runtime register values
    734: 00042623  sw           x0, 12(x8)  # Address depends on runtime register values
    738: 00042823  sw           x0, 16(x8)  # Address depends on runtime register values
    73c: 00042a23  sw           x0, 20(x8)  # Address depends on runtime register values
    740: 00042c23  sw           x0, 24(x8)  # Address depends on runtime register values
    744: 00042e23  sw           x0, 28(x8)  # Address depends on runtime register values
    748: 02040413  addi         x8, x8, 32
    74c: ff848493  addi         x9, x9, -8
    750: fc049ce3  bne          x9, x0, 0x00000728  # target 0x00000728
    754: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    758: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    75c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888
    760: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    764: 008383b3  add          x7, x7, x8
    768: 0001d4b7  lui          x9, 0x0001d  # x9 = 0x0001d000
    76c: fc048493  addi         x9, x9, -64  # x9 = 0x0001cfc0
    770: 0093e663  bltu         x7, x9, 0x0000077c  # target 0x0000077c
    774: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    778: 40a383b3  sub          x7, x7, x10
loc_77c:
    77c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    780: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    784: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
    788: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    78c: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    790: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c
    794: 00138393  addi         x7, x7, 1
    798: 01039393  slli         x7, x7, 16
    79c: 0103d393  srli         x7, x7, 16
    7a0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7a4: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    7a8: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c; write runtime value
    7ac: ffb4d437  lui          x8, 0xffb4d  # x8 = 0xffb4d000
    7b0: 02840413  addi         x8, x8, 40  # x8 = 0xffb4d028
    7b4: 00742023  sw           x7, 0(x8)  # 0xffb4d028; write runtime value
    7b8: 0ff0000f  fence        0xf, 0xf
    7bc: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    7c0: 89460613  addi         x12, x12, -1900  # x12 = 0xffb00894 · riscv_local_mem + 0x894
    7c4: 00062383  lw           x7, 0(x12)  # riscv_local_mem + 0x894 · 0xffb00894
loc_7c8:
    7c8: ffb4c637  lui          x12, 0xffb4c  # x12 = 0xffb4c000
    7cc: 02060613  addi         x12, x12, 32  # x12 = 0xffb4c020
    7d0: 00065403  lhu          x8, 0(x12)  # 0xffb4c020
    7d4: 408384b3  sub          x9, x7, x8
    7d8: 01049493  slli         x9, x9, 16
    7dc: 0104d493  srli         x9, x9, 16
    7e0: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
    7e4: 40950533  sub          x10, x10, x9
    7e8: 00100593  addi         x11, x0, 1  # x11 = 0x00000001
    7ec: 00b57663  bgeu         x10, x11, 0x000007f8  # target 0x000007f8
    7f0: 0ff0000f  fence        0xf, 0xf
    7f4: fd5ff06f  jal          x0, 0x000007c8  # target 0x000007c8
loc_7f8:
    7f8: 0ff0000f  fence        0xf, 0xf
    7fc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    800: 89040413  addi         x8, x8, -1904  # x8 = 0xffb00890 · riscv_local_mem + 0x890
    804: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x890 · 0xffb00890
    808: 00038413  addi         x8, x7, 0
    80c: 40000493  addi         x9, x0, 1024  # x9 = 0x00000400
loc_810:
    810: 00042023  sw           x0, 0(x8)  # Address depends on runtime register values
    814: 00042223  sw           x0, 4(x8)  # Address depends on runtime register values
    818: 00042423  sw           x0, 8(x8)  # Address depends on runtime register values
    81c: 00042623  sw           x0, 12(x8)  # Address depends on runtime register values
    820: 00042823  sw           x0, 16(x8)  # Address depends on runtime register values
    824: 00042a23  sw           x0, 20(x8)  # Address depends on runtime register values
    828: 00042c23  sw           x0, 24(x8)  # Address depends on runtime register values
    82c: 00042e23  sw           x0, 28(x8)  # Address depends on runtime register values
    830: 02040413  addi         x8, x8, 32
    834: ff848493  addi         x9, x9, -8
    838: fc049ce3  bne          x9, x0, 0x00000810  # target 0x00000810
    83c: 00030413  addi         x8, x6, 0
    840: 02000493  addi         x9, x0, 32  # x9 = 0x00000020
    844: ff800537  lui          x10, 0xff800  # x10 = 0xff800000
loc_848:
    848: 02947463  bgeu         x8, x9, 0x00000870  # target 0x00000870
    84c: 00445593  srli         x11, x8, 4
    850: 00a59593  slli         x11, x11, 10
    854: 00f47613  andi         x12, x8, 15
    858: 00261613  slli         x12, x12, 2
    85c: 00c586b3  add          x13, x11, x12
    860: 00d38733  add          x14, x7, x13
    864: 00a72023  sw           x10, 0(x14)  # Address depends on runtime register values
    868: 00140413  addi         x8, x8, 1
    86c: fddff06f  jal          x0, 0x00000848  # target 0x00000848
loc_870:
    870: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    874: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
    878: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890
    87c: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    880: 008383b3  add          x7, x7, x8
    884: 0001c4b7  lui          x9, 0x0001c  # x9 = 0x0001c000
    888: fc048493  addi         x9, x9, -64  # x9 = 0x0001bfc0
    88c: 0093e663  bltu         x7, x9, 0x00000898  # target 0x00000898
    890: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    894: 40a383b3  sub          x7, x7, x10
loc_898:
    898: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    89c: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
    8a0: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890; write runtime value
    8a4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    8a8: 89440413  addi         x8, x8, -1900  # x8 = 0xffb00894 · riscv_local_mem + 0x894
    8ac: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x894 · 0xffb00894
    8b0: 00138393  addi         x7, x7, 1
    8b4: 01039393  slli         x7, x7, 16
    8b8: 0103d393  srli         x7, x7, 16
    8bc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    8c0: 89440413  addi         x8, x8, -1900  # x8 = 0xffb00894 · riscv_local_mem + 0x894
    8c4: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x894 · 0xffb00894; write runtime value
    8c8: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    8cc: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    8d0: 00742023  sw           x7, 0(x8)  # 0xffb4c028; write runtime value
    8d4: 0ff0000f  fence        0xf, 0xf
    8d8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    8dc: 00028413  addi         x8, x5, 0
loc_8e0:
    8e0: 3e83f063  bgeu         x7, x8, 0x00000cc0  # target 0x00000cc0
    8e4: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    8e8: 89c70713  addi         x14, x14, -1892  # x14 = 0xffb0089c · riscv_local_mem + 0x89c
    8ec: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x89c · 0xffb0089c
loc_8f0:
    8f0: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    8f4: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    8f8: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    8fc: 40a485b3  sub          x11, x9, x10
    900: 01059593  slli         x11, x11, 16
    904: 0105d593  srli         x11, x11, 16
    908: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    90c: 40b60633  sub          x12, x12, x11
    910: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    914: 00d67663  bgeu         x12, x13, 0x00000920  # target 0x00000920
    918: 0ff0000f  fence        0xf, 0xf
    91c: fd5ff06f  jal          x0, 0x000008f0  # target 0x000008f0
loc_920:
    920: 0ff0000f  fence        0xf, 0xf
    924: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    928: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    92c: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898
    930: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    934: 00a484b3  add          x9, x9, x10
    938: 000115b7  lui          x11, 0x00011  # x11 = 0x00011000
    93c: fc058593  addi         x11, x11, -64  # x11 = 0x00010fc0
    940: 00b4e663  bltu         x9, x11, 0x0000094c  # target 0x0000094c
    944: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    948: 40c484b3  sub          x9, x9, x12
loc_94c:
    94c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    950: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    954: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898; write runtime value
    958: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    95c: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    960: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c
    964: 00448493  addi         x9, x9, 4
    968: 01049493  slli         x9, x9, 16
    96c: 0104d493  srli         x9, x9, 16
    970: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    974: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    978: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c; write runtime value
    97c: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    980: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    984: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    988: 0ff0000f  fence        0xf, 0xf
    98c: 00225493  srli         x9, x4, 2
    990: 00a49493  slli         x9, x9, 10
    994: 00239513  slli         x10, x7, 2
    998: 00a484b3  add          x9, x9, x10
    99c: 328000ef  jal          x1, 0x00000cc4  # target 0x00000cc4; x1 = 0x000009a0
    9a0: 340000ef  jal          x1, 0x00000ce0  # target 0x00000ce0; x1 = 0x000009a4
    9a4: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    9a8: 8a480813  addi         x16, x16, -1884  # x16 = 0xffb008a4 · riscv_local_mem + 0x8a4
    9ac: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x8a4 · 0xffb008a4
loc_9b0:
    9b0: ffb49837  lui          x16, 0xffb49  # x16 = 0xffb49000
    9b4: 02080813  addi         x16, x16, 32  # x16 = 0xffb49020
    9b8: 00085603  lhu          x12, 0(x16)  # 0xffb49020
    9bc: 40c586b3  sub          x13, x11, x12
    9c0: 01069693  slli         x13, x13, 16
    9c4: 0106d693  srli         x13, x13, 16
    9c8: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    9cc: 40d70733  sub          x14, x14, x13
    9d0: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    9d4: 00f77663  bgeu         x14, x15, 0x000009e0  # target 0x000009e0
    9d8: 0ff0000f  fence        0xf, 0xf
    9dc: fd5ff06f  jal          x0, 0x000009b0  # target 0x000009b0
loc_9e0:
    9e0: 0ff0000f  fence        0xf, 0xf
    9e4: 00048593  addi         x11, x9, 0
    9e8: 00058f93  addi         x31, x11, 0
    9ec: 5a0000ef  jal          x1, 0x00000f8c  # target 0x00000f8c; x1 = 0x000009f0
    9f0: 000a8613  addi         x12, x21, 0
    9f4: 000b0693  addi         x13, x22, 0
    9f8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    9fc: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    a00: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    a04: 00060f93  addi         x31, x12, 0
    a08: 00068f13  addi         x30, x13, 0
    a0c: 00070e93  addi         x29, x14, 0
    a10: 338000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000a14
    a14: 00148593  addi         x11, x9, 1
    a18: 00058f93  addi         x31, x11, 0
    a1c: 570000ef  jal          x1, 0x00000f8c  # target 0x00000f8c; x1 = 0x00000a20
    a20: 000a8613  addi         x12, x21, 0
    a24: 000b0693  addi         x13, x22, 0
    a28: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a2c: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    a30: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    a34: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a38: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    a3c: 00f70733  add          x14, x14, x15
    a40: 00060f93  addi         x31, x12, 0
    a44: 00068f13  addi         x30, x13, 0
    a48: 00070e93  addi         x29, x14, 0
    a4c: 2fc000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000a50
    a50: 00248593  addi         x11, x9, 2
    a54: 00058f93  addi         x31, x11, 0
    a58: 534000ef  jal          x1, 0x00000f8c  # target 0x00000f8c; x1 = 0x00000a5c
    a5c: 000a8613  addi         x12, x21, 0
    a60: 000b0693  addi         x13, x22, 0
    a64: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a68: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    a6c: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    a70: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a74: 00f70733  add          x14, x14, x15
    a78: 00060f93  addi         x31, x12, 0
    a7c: 00068f13  addi         x30, x13, 0
    a80: 00070e93  addi         x29, x14, 0
    a84: 2c4000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000a88
    a88: 00348593  addi         x11, x9, 3
    a8c: 00058f93  addi         x31, x11, 0
    a90: 4fc000ef  jal          x1, 0x00000f8c  # target 0x00000f8c; x1 = 0x00000a94
    a94: 000a8613  addi         x12, x21, 0
    a98: 000b0693  addi         x13, x22, 0
    a9c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    aa0: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    aa4: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    aa8: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    aac: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    ab0: 00f70733  add          x14, x14, x15
    ab4: 00060f93  addi         x31, x12, 0
    ab8: 00068f13  addi         x30, x13, 0
    abc: 00070e93  addi         x29, x14, 0
    ac0: 288000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000ac4
    ac4: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    ac8: 8ac80813  addi         x16, x16, -1876  # x16 = 0xffb008ac · riscv_local_mem + 0x8ac
    acc: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x8ac · 0xffb008ac
loc_ad0:
    ad0: ffb4a837  lui          x16, 0xffb4a  # x16 = 0xffb4a000
    ad4: 02080813  addi         x16, x16, 32  # x16 = 0xffb4a020
    ad8: 00085603  lhu          x12, 0(x16)  # 0xffb4a020
    adc: 40c586b3  sub          x13, x11, x12
    ae0: 01069693  slli         x13, x13, 16
    ae4: 0106d693  srli         x13, x13, 16
    ae8: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    aec: 40d70733  sub          x14, x14, x13
    af0: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    af4: 00f77663  bgeu         x14, x15, 0x00000b00  # target 0x00000b00
    af8: 0ff0000f  fence        0xf, 0xf
    afc: fd5ff06f  jal          x0, 0x00000ad0  # target 0x00000ad0
loc_b00:
    b00: 0ff0000f  fence        0xf, 0xf
    b04: 00048593  addi         x11, x9, 0
    b08: 00058f93  addi         x31, x11, 0
    b0c: 4cc000ef  jal          x1, 0x00000fd8  # target 0x00000fd8; x1 = 0x00000b10
    b10: 000a8613  addi         x12, x21, 0
    b14: 000b0693  addi         x13, x22, 0
    b18: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b1c: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    b20: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    b24: 00060f93  addi         x31, x12, 0
    b28: 00068f13  addi         x30, x13, 0
    b2c: 00070e93  addi         x29, x14, 0
    b30: 218000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000b34
    b34: 00148593  addi         x11, x9, 1
    b38: 00058f93  addi         x31, x11, 0
    b3c: 49c000ef  jal          x1, 0x00000fd8  # target 0x00000fd8; x1 = 0x00000b40
    b40: 000a8613  addi         x12, x21, 0
    b44: 000b0693  addi         x13, x22, 0
    b48: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b4c: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    b50: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    b54: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    b58: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    b5c: 00f70733  add          x14, x14, x15
    b60: 00060f93  addi         x31, x12, 0
    b64: 00068f13  addi         x30, x13, 0
    b68: 00070e93  addi         x29, x14, 0
    b6c: 1dc000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000b70
    b70: 00248593  addi         x11, x9, 2
    b74: 00058f93  addi         x31, x11, 0
    b78: 460000ef  jal          x1, 0x00000fd8  # target 0x00000fd8; x1 = 0x00000b7c
    b7c: 000a8613  addi         x12, x21, 0
    b80: 000b0693  addi         x13, x22, 0
    b84: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b88: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    b8c: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    b90: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    b94: 00f70733  add          x14, x14, x15
    b98: 00060f93  addi         x31, x12, 0
    b9c: 00068f13  addi         x30, x13, 0
    ba0: 00070e93  addi         x29, x14, 0
    ba4: 1a4000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000ba8
    ba8: 00348593  addi         x11, x9, 3
    bac: 00058f93  addi         x31, x11, 0
    bb0: 428000ef  jal          x1, 0x00000fd8  # target 0x00000fd8; x1 = 0x00000bb4
    bb4: 000a8613  addi         x12, x21, 0
    bb8: 000b0693  addi         x13, x22, 0
    bbc: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    bc0: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    bc4: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    bc8: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    bcc: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    bd0: 00f70733  add          x14, x14, x15
    bd4: 00060f93  addi         x31, x12, 0
    bd8: 00068f13  addi         x30, x13, 0
    bdc: 00070e93  addi         x29, x14, 0
    be0: 168000ef  jal          x1, 0x00000d48  # target 0x00000d48; x1 = 0x00000be4
    be4: 0fc000ef  jal          x1, 0x00000ce0  # target 0x00000ce0; x1 = 0x00000be8
    be8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    bec: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    bf0: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    bf4: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    bf8: 00c585b3  add          x11, x11, x12
    bfc: 000156b7  lui          x13, 0x00015  # x13 = 0x00015000
    c00: fc068693  addi         x13, x13, -64  # x13 = 0x00014fc0
    c04: 00d5e663  bltu         x11, x13, 0x00000c10  # target 0x00000c10
    c08: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    c0c: 40e585b3  sub          x11, x11, x14
loc_c10:
    c10: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    c14: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    c18: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0; write runtime value
    c1c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    c20: 8a460613  addi         x12, x12, -1884  # x12 = 0xffb008a4 · riscv_local_mem + 0x8a4
    c24: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x8a4 · 0xffb008a4
    c28: 00458593  addi         x11, x11, 4
    c2c: 01059593  slli         x11, x11, 16
    c30: 0105d593  srli         x11, x11, 16
    c34: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    c38: 8a460613  addi         x12, x12, -1884  # x12 = 0xffb008a4 · riscv_local_mem + 0x8a4
    c3c: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x8a4 · 0xffb008a4; write runtime value
    c40: ffb49637  lui          x12, 0xffb49  # x12 = 0xffb49000
    c44: 02860613  addi         x12, x12, 40  # x12 = 0xffb49028
    c48: 00b62023  sw           x11, 0(x12)  # 0xffb49028; write runtime value
    c4c: 0ff0000f  fence        0xf, 0xf
    c50: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    c54: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    c58: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    c5c: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    c60: 00c585b3  add          x11, x11, x12
    c64: 000196b7  lui          x13, 0x00019  # x13 = 0x00019000
    c68: fc068693  addi         x13, x13, -64  # x13 = 0x00018fc0
    c6c: 00d5e663  bltu         x11, x13, 0x00000c78  # target 0x00000c78
    c70: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    c74: 40e585b3  sub          x11, x11, x14
loc_c78:
    c78: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    c7c: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    c80: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8; write runtime value
    c84: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    c88: 8ac60613  addi         x12, x12, -1876  # x12 = 0xffb008ac · riscv_local_mem + 0x8ac
    c8c: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x8ac · 0xffb008ac
    c90: 00458593  addi         x11, x11, 4
    c94: 01059593  slli         x11, x11, 16
    c98: 0105d593  srli         x11, x11, 16
    c9c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    ca0: 8ac60613  addi         x12, x12, -1876  # x12 = 0xffb008ac · riscv_local_mem + 0x8ac
    ca4: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x8ac · 0xffb008ac; write runtime value
    ca8: ffb4a637  lui          x12, 0xffb4a  # x12 = 0xffb4a000
    cac: 02860613  addi         x12, x12, 40  # x12 = 0xffb4a028
    cb0: 00b62023  sw           x11, 0(x12)  # 0xffb4a028; write runtime value
    cb4: 0ff0000f  fence        0xf, 0xf
    cb8: 00138393  addi         x7, x7, 1
    cbc: c25ff06f  jal          x0, 0x000008e0  # target 0x000008e0
loc_cc0:
    cc0: 3640006f  jal          x0, 0x00001024  # target 0x00001024
loc_cc4:
    cc4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    cc8: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    ccc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    cd0: 000a0463  beq          x20, x0, 0x00000cd8  # target 0x00000cd8
    cd4: ff1ff06f  jal          x0, 0x00000cc4  # target 0x00000cc4
loc_cd8:
    cd8: 0ff0000f  fence        0xf, 0xf
    cdc: 00008067  jalr         x0, 0(x1)
loc_ce0:
    ce0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    ce4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    ce8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    cec: 000a0463  beq          x20, x0, 0x00000cf4  # target 0x00000cf4
    cf0: ff1ff06f  jal          x0, 0x00000ce0  # target 0x00000ce0
loc_cf4:
    cf4: 0ff0000f  fence        0xf, 0xf
    cf8: 00008067  jalr         x0, 0(x1)
loc_cfc:
    cfc: 7a400a93  addi         x21, x0, 1956  # x21 = 0x000007a4
    d00: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_cos; 0x000007a4
    d04: 007a7d13  andi         x26, x20, 7
    d08: ff8a7a13  andi         x20, x20, -8
    d0c: 01af8ab3  add          x21, x31, x26
    d10: 007afb93  andi         x23, x21, 7
    d14: 003ada93  srli         x21, x21, 3
    d18: 00ba9a93  slli         x21, x21, 11
    d1c: 014a8ab3  add          x21, x21, x20
    d20: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d20
    d24: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d38
    d28: 001b9b93  slli         x23, x23, 1
    d2c: 017b0b33  add          x22, x22, x23
    d30: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d34: 00008067  jalr         x0, 0(x1)
    d38: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    d3c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d40: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    d44: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d48:
    d48: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    d4c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    d50: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    d54: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    d58: 015a6463  bltu         x20, x21, 0x00000d60  # target 0x00000d60
    d5c: fedff06f  jal          x0, 0x00000d48  # target 0x00000d48
loc_d60:
    d60: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    d64: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    d68: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    d6c: 014a1a13  slli         x20, x20, 20
    d70: 014a5a13  srli         x20, x20, 20
    d74: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_d78:
    d78: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    d7c: 000b0463  beq          x22, x0, 0x00000d84  # target 0x00000d84
    d80: ff9ff06f  jal          x0, 0x00000d78  # target 0x00000d78
loc_d84:
    d84: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    d88: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    d8c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    d90: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    d94: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    d98: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    d9c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    da0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    da4: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    da8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    dac: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    db0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    db4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    db8: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    dbc: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    dc0: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    dc4: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    dc8: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    dcc: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    dd0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    dd4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    dd8: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_ddc:
    ddc: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    de0: 000b0463  beq          x22, x0, 0x00000de8  # target 0x00000de8
    de4: ff9ff06f  jal          x0, 0x00000ddc  # target 0x00000ddc
loc_de8:
    de8: 00008067  jalr         x0, 0(x1)
loc_dec:
    dec: 7a800a93  addi         x21, x0, 1960  # x21 = 0x000007a8
    df0: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_sin; 0x000007a8
    df4: 007a7d13  andi         x26, x20, 7
    df8: ff8a7a13  andi         x20, x20, -8
    dfc: 01af8ab3  add          x21, x31, x26
    e00: 007afb93  andi         x23, x21, 7
    e04: 003ada93  srli         x21, x21, 3
    e08: 00ba9a93  slli         x21, x21, 11
    e0c: 014a8ab3  add          x21, x21, x20
    e10: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e10
    e14: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e28
    e18: 001b9b93  slli         x23, x23, 1
    e1c: 017b0b33  add          x22, x22, x23
    e20: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e24: 00008067  jalr         x0, 0(x1)
    e28: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    e2c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e30: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    e34: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_e38:
    e38: 79800a93  addi         x21, x0, 1944  # x21 = 0x00000798
    e3c: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_q_compact; 0x00000798
    e40: 007a7d13  andi         x26, x20, 7
    e44: ff8a7a13  andi         x20, x20, -8
    e48: 01af8ab3  add          x21, x31, x26
    e4c: 007afb93  andi         x23, x21, 7
    e50: 003ada93  srli         x21, x21, 3
    e54: 00ba9a93  slli         x21, x21, 11
    e58: 014a8ab3  add          x21, x21, x20
    e5c: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e5c
    e60: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e74
    e64: 001b9b93  slli         x23, x23, 1
    e68: 017b0b33  add          x22, x22, x23
    e6c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e70: 00008067  jalr         x0, 0(x1)
    e74: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    e78: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e7c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    e80: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_e84:
    e84: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    e88: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_k_compact; 0x0000079c
    e8c: 007a7d13  andi         x26, x20, 7
    e90: ff8a7a13  andi         x20, x20, -8
    e94: 01af8ab3  add          x21, x31, x26
    e98: 007afb93  andi         x23, x21, 7
    e9c: 003ada93  srli         x21, x21, 3
    ea0: 00ba9a93  slli         x21, x21, 11
    ea4: 014a8ab3  add          x21, x21, x20
    ea8: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000ea8
    eac: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000ec0
    eb0: 001b9b93  slli         x23, x23, 1
    eb4: 017b0b33  add          x22, x22, x23
    eb8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    ebc: 00008067  jalr         x0, 0(x1)
    ec0: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    ec4: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    ec8: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    ecc: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_ed0:
    ed0: 7a000a93  addi         x21, x0, 1952  # x21 = 0x000007a0
    ed4: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_v_compact; 0x000007a0
    ed8: 007a7d13  andi         x26, x20, 7
    edc: ff8a7a13  andi         x20, x20, -8
    ee0: 01af8ab3  add          x21, x31, x26
    ee4: 007afb93  andi         x23, x21, 7
    ee8: 003ada93  srli         x21, x21, 3
    eec: 00ba9a93  slli         x21, x21, 11
    ef0: 014a8ab3  add          x21, x21, x20
    ef4: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000ef4
    ef8: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000f0c
    efc: 001b9b93  slli         x23, x23, 1
    f00: 017b0b33  add          x22, x22, x23
    f04: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    f08: 00008067  jalr         x0, 0(x1)
    f0c: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    f10: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    f14: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    f18: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_f1c:
    f1c: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    f20: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    f24: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    f28: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    f2c: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    f30: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    f34: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    f38: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    f3c: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    f40: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    f44: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    f48: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    f4c: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    f50: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    f54: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    f58: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    f5c: 020f8f93  addi         x31, x31, 32
    f60: 020f0f13  addi         x30, x30, 32
    f64: ff8e8e93  addi         x29, x29, -8
    f68: fa0e9ae3  bne          x29, x0, 0x00000f1c  # target 0x00000f1c
    f6c: 00008067  jalr         x0, 0(x1)
loc_f70:
    f70: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    f74: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    f78: 004f8f93  addi         x31, x31, 4
    f7c: 004f0f13  addi         x30, x30, 4
    f80: fffe8e93  addi         x29, x29, -1
    f84: fe0e96e3  bne          x29, x0, 0x00000f70  # target 0x00000f70
    f88: 00008067  jalr         x0, 0(x1)
loc_f8c:
    f8c: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    f90: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    f94: 007a7d13  andi         x26, x20, 7
    f98: ff8a7a13  andi         x20, x20, -8
    f9c: 01af8ab3  add          x21, x31, x26
    fa0: 007afb93  andi         x23, x21, 7
    fa4: 003ada93  srli         x21, x21, 3
    fa8: 00ba9a93  slli         x21, x21, 11
    fac: 014a8ab3  add          x21, x21, x20
    fb0: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000fb0
    fb4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000fc8
    fb8: 001b9b93  slli         x23, x23, 1
    fbc: 017b0b33  add          x22, x22, x23
    fc0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    fc4: 00008067  jalr         x0, 0(x1)
    fc8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    fcc: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    fd0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    fd4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_fd8:
    fd8: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    fdc: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    fe0: 007a7d13  andi         x26, x20, 7
    fe4: ff8a7a13  andi         x20, x20, -8
    fe8: 01af8ab3  add          x21, x31, x26
    fec: 007afb93  andi         x23, x21, 7
    ff0: 003ada93  srli         x21, x21, 3
    ff4: 00ba9a93  slli         x21, x21, 11
    ff8: 014a8ab3  add          x21, x21, x20
    ffc: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000ffc
   1000: 018b0b13  addi         x22, x22, 24  # x22 = 0x00001014
   1004: 001b9b93  slli         x23, x23, 1
   1008: 017b0b33  add          x22, x22, x23
   100c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   1010: 00008067  jalr         x0, 0(x1)
   1014: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
   1018: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   101c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
   1020: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
   1024:           j FW_BRISC+4   # return to firmware, linked at install
