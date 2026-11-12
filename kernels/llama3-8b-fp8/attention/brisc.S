# llama3 8b-fp8 decode: attention, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=e2e_attention_partials, 0xe904=attention_core, 0xe908=attention_phase
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000202b7  lui          x5, 0x00020  # x5 = 0x00020000
      c: 88028293  addi         x5, x5, -1920  # x5 = 0x0001f880
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0001f880
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     28: 000222b7  lui          x5, 0x00022  # x5 = 0x00022000
     2c: 08028293  addi         x5, x5, 128  # x5 = 0x00022080
     30: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00022080
     34: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     38: 88420213  addi         x4, x4, -1916  # x4 = 0xffb00884 · riscv_local_mem + 0x884
     3c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     40: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     44: 88838393  addi         x7, x7, -1912  # x7 = 0xffb00888 · riscv_local_mem + 0x888
     48: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
     4c: 08040413  addi         x8, x8, 128  # x8 = 0x0000f080
     50: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x888 · 0xffb00888; write 0x0000f080
     54: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     58: 88c38393  addi         x7, x7, -1908  # x7 = 0xffb0088c · riscv_local_mem + 0x88c
     5c: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x88c · 0xffb0088c; write 0x00000000
     60: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     64: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
     68: 00011637  lui          x12, 0x00011  # x12 = 0x00011000
     6c: 08060613  addi         x12, x12, 128  # x12 = 0x00011080
     70: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890; write 0x00011080
     74: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     78: 89458593  addi         x11, x11, -1900  # x11 = 0xffb00894 · riscv_local_mem + 0x894
     7c: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x894 · 0xffb00894; write 0x00000000
     80: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     84: 89858593  addi         x11, x11, -1896  # x11 = 0xffb00898 · riscv_local_mem + 0x898
     88: 00015637  lui          x12, 0x00015  # x12 = 0x00015000
     8c: 08060613  addi         x12, x12, 128  # x12 = 0x00015080
     90: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x898 · 0xffb00898; write 0x00015080
     94: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     98: 89c58593  addi         x11, x11, -1892  # x11 = 0xffb0089c · riscv_local_mem + 0x89c
     9c: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x89c · 0xffb0089c; write 0x00000000
     a0: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     a4: 90830313  addi         x6, x6, -1784  # x6 = 0x0000e908
     a8: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x0000e908
     ac: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     b0: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     b4: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     b8: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     bc: 0063fa63  bgeu         x7, x6, 0x000000d0  # target 0x000000d0
     c0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     c4: 08000393  addi         x7, x0, 128  # x7 = 0x00000080
     c8: 0063f463  bgeu         x7, x6, 0x000000d0  # target 0x000000d0
     cc: 00c00293  addi         x5, x0, 12  # x5 = 0x0000000c
loc_d0:
     d0: 2a527ce3  bgeu         x4, x5, 0x00000b88  # target 0x00000b88
     d4: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
     d8: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
     dc: 00325293  srli         x5, x4, 3
     e0: 00727313  andi         x6, x4, 7
     e4: 00731313  slli         x6, x6, 7
     e8: 00131313  slli         x6, x6, 1
     ec: 2a1000ef  jal          x1, 0x00000b8c  # target 0x00000b8c; x1 = 0x000000f0
     f0: 2b9000ef  jal          x1, 0x00000ba8  # target 0x00000ba8; x1 = 0x000000f4
     f4: 00028f93  addi         x31, x5, 0
     f8: 2cd000ef  jal          x1, 0x00000bc4  # target 0x00000bc4; x1 = 0x000000fc
     fc: 000a8393  addi         x7, x21, 0
    100: 000b0413  addi         x8, x22, 0
    104: 00038f93  addi         x31, x7, 0
    108: 00040f13  addi         x30, x8, 0
    10c: 00037eb7  lui          x29, 0x00037  # x29 = 0x00037000 · arc_apb_reset_unit + 0x7000
    110: 080e8e93  addi         x29, x29, 128  # x29 = 0x00037080 · arc_apb_reset_unit + 0x7080
    114: 2fd000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x00000118
    118: 00028f93  addi         x31, x5, 0
    11c: 399000ef  jal          x1, 0x00000cb4  # target 0x00000cb4; x1 = 0x00000120
    120: 000a8393  addi         x7, x21, 0
    124: 000b0413  addi         x8, x22, 0
    128: 00038f93  addi         x31, x7, 0
    12c: 00040f13  addi         x30, x8, 0
    130: 00038eb7  lui          x29, 0x00038  # x29 = 0x00038000 · arc_apb_reset_unit + 0x8000
    134: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00037880 · arc_apb_reset_unit + 0x7880
    138: 2d9000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x0000013c
    13c: 26d000ef  jal          x1, 0x00000ba8  # target 0x00000ba8; x1 = 0x00000140
    140: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    144: 90448493  addi         x9, x9, -1788  # x9 = 0x0000e904
    148: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x0000e904
    14c: 00c00493  addi         x9, x0, 12  # x9 = 0x0000000c
    150: 02945433  divu         x8, x8, x9
    154: 00941413  slli         x8, x8, 9
    158: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
loc_15c:
    15c: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    160: ac068693  addi         x13, x13, -1344  # x13 = 0x00000ac0
    164: 00d47c63  bgeu         x8, x13, 0x0000017c  # target 0x0000017c
    168: 02b00613  addi         x12, x0, 43  # x12 = 0x0000002b
    16c: 02c454b3  divu         x9, x8, x12
    170: 02c485b3  mul          x11, x9, x12
    174: 40b405b3  sub          x11, x8, x11
    178: 01c0006f  jal          x0, 0x00000194  # target 0x00000194
loc_17c:
    17c: 40d406b3  sub          x13, x8, x13
    180: 02a00613  addi         x12, x0, 42  # x12 = 0x0000002a
    184: 02c6d4b3  divu         x9, x13, x12
    188: 02c485b3  mul          x11, x9, x12
    18c: 40b685b3  sub          x11, x13, x11
    190: 04048493  addi         x9, x9, 64
loc_194:
    194: 07f40513  addi         x10, x8, 127
    198: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    19c: ac078793  addi         x15, x15, -1344  # x15 = 0x00000ac0
    1a0: 00f57c63  bgeu         x10, x15, 0x000001b8  # target 0x000001b8
    1a4: 02b00713  addi         x14, x0, 43  # x14 = 0x0000002b
    1a8: 02e55633  divu         x12, x10, x14
    1ac: 02e606b3  mul          x13, x12, x14
    1b0: 40d506b3  sub          x13, x10, x13
    1b4: 01c0006f  jal          x0, 0x000001d0  # target 0x000001d0
loc_1b8:
    1b8: 40f507b3  sub          x15, x10, x15
    1bc: 02a00713  addi         x14, x0, 42  # x14 = 0x0000002a
    1c0: 02e7d633  divu         x12, x15, x14
    1c4: 02e606b3  mul          x13, x12, x14
    1c8: 40d786b3  sub          x13, x15, x13
    1cc: 04060613  addi         x12, x12, 64
loc_1d0:
    1d0: 00048513  addi         x10, x9, 0
    1d4: 1b9000ef  jal          x1, 0x00000b8c  # target 0x00000b8c; x1 = 0x000001d8
    1d8: 1d1000ef  jal          x1, 0x00000ba8  # target 0x00000ba8; x1 = 0x000001dc
    1dc: 00023737  lui          x14, 0x00023  # x14 = 0x00023000
    1e0: 88070713  addi         x14, x14, -1920  # x14 = 0x00022880
loc_1e4:
    1e4: 00050f93  addi         x31, x10, 0
    1e8: 319000ef  jal          x1, 0x00000d00  # target 0x00000d00; x1 = 0x000001ec
    1ec: 000a8793  addi         x15, x21, 0
    1f0: 000b0813  addi         x16, x22, 0
    1f4: 00078f93  addi         x31, x15, 0
    1f8: 00080f13  addi         x30, x16, 0
    1fc: 00070e93  addi         x29, x14, 0
    200: 211000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x00000204
    204: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    208: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    20c: 00f70733  add          x14, x14, x15
    210: 00150513  addi         x10, x10, 1
    214: fca678e3  bgeu         x12, x10, 0x000001e4  # target 0x000001e4
    218: 191000ef  jal          x1, 0x00000ba8  # target 0x00000ba8; x1 = 0x0000021c
    21c: 00048513  addi         x10, x9, 0
    220: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    224: 00839693  slli         x13, x7, 8
    228: 00020737  lui          x14, 0x00020  # x14 = 0x00020000
    22c: 88070713  addi         x14, x14, -1920  # x14 = 0x0001f880
    230: 00e686b3  add          x13, x13, x14
loc_234:
    234: 02a00713  addi         x14, x0, 42  # x14 = 0x0000002a
    238: 04000793  addi         x15, x0, 64  # x15 = 0x00000040
    23c: 00f57463  bgeu         x10, x15, 0x00000244  # target 0x00000244
    240: 00170713  addi         x14, x14, 1  # x14 = 0x0000002b
loc_244:
    244: 40b70733  sub          x14, x14, x11
    248: 00f5f793  andi         x15, x11, 15
    24c: 40f007b3  sub          x15, x0, x15
    250: 01078793  addi         x15, x15, 16
    254: 00e7f463  bgeu         x15, x14, 0x0000025c  # target 0x0000025c
    258: 00078713  addi         x14, x15, 0
loc_25c:
    25c: 03f67793  andi         x15, x12, 63
    260: 40f007b3  sub          x15, x0, x15
    264: 04078793  addi         x15, x15, 64
    268: 00e7f463  bgeu         x15, x14, 0x00000270  # target 0x00000270
    26c: 00078713  addi         x14, x15, 0
loc_270:
    270: 40950833  sub          x16, x10, x9
    274: 00b81813  slli         x16, x16, 11
    278: 00f5f793  andi         x15, x11, 15
    27c: 00179793  slli         x15, x15, 1
    280: 0105fa13  andi         x20, x11, 16
    284: 005a1a13  slli         x20, x20, 5
    288: 0147e7b3  or           x15, x15, x20
    28c: 1e05fa13  andi         x20, x11, 480
    290: 0147e7b3  or           x15, x15, x20
    294: 0095da13  srli         x20, x11, 9
    298: 00aa1a13  slli         x20, x20, 10
    29c: 0147e7b3  or           x15, x15, x20
    2a0: 00f80833  add          x16, x16, x15
    2a4: 00023a37  lui          x20, 0x00023  # x20 = 0x00023000
    2a8: 880a0a13  addi         x20, x20, -1920  # x20 = 0x00022880
    2ac: 01480833  add          x16, x16, x20
    2b0: 00161893  slli         x17, x12, 1
    2b4: 00d888b3  add          x17, x17, x13
    2b8: 04064913  xori         x18, x12, 64
    2bc: 00191913  slli         x18, x18, 1
    2c0: 00d90933  add          x18, x18, x13
    2c4: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2c8: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    2cc: 01490933  add          x18, x18, x20
    2d0: 04067993  andi         x19, x12, 64
    2d4: 00999993  slli         x19, x19, 9
    2d8: 00080f93  addi         x31, x16, 0
    2dc: 00088f13  addi         x30, x17, 0
    2e0: 00090e93  addi         x29, x18, 0
    2e4: 00070e13  addi         x28, x14, 0
    2e8: 00098d93  addi         x27, x19, 0
loc_2ec:
    2ec: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    2f0: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    2f4: 01ba4a33  xor          x20, x20, x27
    2f8: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    2fc: 002f8f93  addi         x31, x31, 2
    300: 002f0f13  addi         x30, x30, 2
    304: 002e8e93  addi         x29, x29, 2
    308: fffe0e13  addi         x28, x28, -1
    30c: fe0e10e3  bne          x28, x0, 0x000002ec  # target 0x000002ec
    310: 00e60633  add          x12, x12, x14
    314: 00e585b3  add          x11, x11, x14
    318: 02a00793  addi         x15, x0, 42  # x15 = 0x0000002a
    31c: 04000993  addi         x19, x0, 64  # x19 = 0x00000040
    320: 01357463  bgeu         x10, x19, 0x00000328  # target 0x00000328
    324: 00178793  addi         x15, x15, 1  # x15 = 0x0000002b
loc_328:
    328: 00f59663  bne          x11, x15, 0x00000334  # target 0x00000334
    32c: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    330: 00150513  addi         x10, x10, 1
loc_334:
    334: 08000793  addi         x15, x0, 128  # x15 = 0x00000080
    338: eef66ee3  bltu         x12, x15, 0x00000234  # target 0x00000234
    33c: 08040413  addi         x8, x8, 128
    340: 00138393  addi         x7, x7, 1
    344: 00400493  addi         x9, x0, 4  # x9 = 0x00000004
    348: e0939ae3  bne          x7, x9, 0x0000015c  # target 0x0000015c
    34c: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    350: 90448493  addi         x9, x9, -1788  # x9 = 0x0000e904
    354: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x0000e904
    358: 00c00493  addi         x9, x0, 12  # x9 = 0x0000000c
    35c: 02945433  divu         x8, x8, x9
    360: 00045413  srli         x8, x8, 0
    364: 00741413  slli         x8, x8, 7
    368: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    36c: 2c000693  addi         x13, x0, 704  # x13 = 0x000002c0
    370: 00d47c63  bgeu         x8, x13, 0x00000388  # target 0x00000388
    374: 00b00613  addi         x12, x0, 11  # x12 = 0x0000000b
    378: 02c454b3  divu         x9, x8, x12
    37c: 02c485b3  mul          x11, x9, x12
    380: 40b405b3  sub          x11, x8, x11
    384: 01c0006f  jal          x0, 0x000003a0  # target 0x000003a0
loc_388:
    388: 40d406b3  sub          x13, x8, x13
    38c: 00a00613  addi         x12, x0, 10  # x12 = 0x0000000a
    390: 02c6d4b3  divu         x9, x13, x12
    394: 02c485b3  mul          x11, x9, x12
    398: 40b685b3  sub          x11, x13, x11
    39c: 04048493  addi         x9, x9, 64
loc_3a0:
    3a0: 07f40513  addi         x10, x8, 127
    3a4: 2c000793  addi         x15, x0, 704  # x15 = 0x000002c0
    3a8: 00f57c63  bgeu         x10, x15, 0x000003c0  # target 0x000003c0
    3ac: 00b00713  addi         x14, x0, 11  # x14 = 0x0000000b
    3b0: 02e55633  divu         x12, x10, x14
    3b4: 02e606b3  mul          x13, x12, x14
    3b8: 40d506b3  sub          x13, x10, x13
    3bc: 01c0006f  jal          x0, 0x000003d8  # target 0x000003d8
loc_3c0:
    3c0: 40f507b3  sub          x15, x10, x15
    3c4: 00a00713  addi         x14, x0, 10  # x14 = 0x0000000a
    3c8: 02e7d633  divu         x12, x15, x14
    3cc: 02e606b3  mul          x13, x12, x14
    3d0: 40d786b3  sub          x13, x15, x13
    3d4: 04060613  addi         x12, x12, 64
loc_3d8:
    3d8: 00048513  addi         x10, x9, 0
    3dc: 7b0000ef  jal          x1, 0x00000b8c  # target 0x00000b8c; x1 = 0x000003e0
    3e0: 7c8000ef  jal          x1, 0x00000ba8  # target 0x00000ba8; x1 = 0x000003e4
    3e4: 00023737  lui          x14, 0x00023  # x14 = 0x00023000
    3e8: 88070713  addi         x14, x14, -1920  # x14 = 0x00022880
loc_3ec:
    3ec: 00050f93  addi         x31, x10, 0
    3f0: 15d000ef  jal          x1, 0x00000d4c  # target 0x00000d4c; x1 = 0x000003f4
    3f4: 000a8793  addi         x15, x21, 0
    3f8: 000b0813  addi         x16, x22, 0
    3fc: 00078f93  addi         x31, x15, 0
    400: 00080f13  addi         x30, x16, 0
    404: 00070e93  addi         x29, x14, 0
    408: 009000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x0000040c
    40c: 00050f93  addi         x31, x10, 0
    410: 189000ef  jal          x1, 0x00000d98  # target 0x00000d98; x1 = 0x00000414
    414: 000a8793  addi         x15, x21, 0
    418: 000b0813  addi         x16, x22, 0
    41c: 0000a8b7  lui          x17, 0x0000a  # x17 = 0x0000a000
    420: 00e888b3  add          x17, x17, x14
    424: 00078f93  addi         x31, x15, 0
    428: 00080f13  addi         x30, x16, 0
    42c: 00088e93  addi         x29, x17, 0
    430: 7e0000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x00000434
    434: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    438: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    43c: 00f70733  add          x14, x14, x15
    440: 00150513  addi         x10, x10, 1
    444: faa674e3  bgeu         x12, x10, 0x000003ec  # target 0x000003ec
    448: 760000ef  jal          x1, 0x00000ba8  # target 0x00000ba8; x1 = 0x0000044c
    44c: 00048513  addi         x10, x9, 0
    450: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    454: 00839693  slli         x13, x7, 8
    458: 00020737  lui          x14, 0x00020  # x14 = 0x00020000
    45c: 88070713  addi         x14, x14, -1920  # x14 = 0x0001f880
    460: 00e686b3  add          x13, x13, x14
loc_464:
    464: 00a00713  addi         x14, x0, 10  # x14 = 0x0000000a
    468: 04000793  addi         x15, x0, 64  # x15 = 0x00000040
    46c: 00f57463  bgeu         x10, x15, 0x00000474  # target 0x00000474
    470: 00170713  addi         x14, x14, 1  # x14 = 0x0000000b
loc_474:
    474: 40b70733  sub          x14, x14, x11
    478: 00f5f793  andi         x15, x11, 15
    47c: 40f007b3  sub          x15, x0, x15
    480: 01078793  addi         x15, x15, 16
    484: 00e7f463  bgeu         x15, x14, 0x0000048c  # target 0x0000048c
    488: 00078713  addi         x14, x15, 0
loc_48c:
    48c: 03f67793  andi         x15, x12, 63
    490: 40f007b3  sub          x15, x0, x15
    494: 04078793  addi         x15, x15, 64
    498: 00e7f463  bgeu         x15, x14, 0x000004a0  # target 0x000004a0
    49c: 00078713  addi         x14, x15, 0
loc_4a0:
    4a0: 40950833  sub          x16, x10, x9
    4a4: 00b81813  slli         x16, x16, 11
    4a8: 00f5f793  andi         x15, x11, 15
    4ac: 00179793  slli         x15, x15, 1
    4b0: 0105fa13  andi         x20, x11, 16
    4b4: 005a1a13  slli         x20, x20, 5
    4b8: 0147e7b3  or           x15, x15, x20
    4bc: 1e05fa13  andi         x20, x11, 480
    4c0: 0147e7b3  or           x15, x15, x20
    4c4: 0095da13  srli         x20, x11, 9
    4c8: 00aa1a13  slli         x20, x20, 10
    4cc: 0147e7b3  or           x15, x15, x20
    4d0: 00f80833  add          x16, x16, x15
    4d4: 00023a37  lui          x20, 0x00023  # x20 = 0x00023000
    4d8: 880a0a13  addi         x20, x20, -1920  # x20 = 0x00022880
    4dc: 01480833  add          x16, x16, x20
    4e0: 00161893  slli         x17, x12, 1
    4e4: 00d888b3  add          x17, x17, x13
    4e8: 04064913  xori         x18, x12, 64
    4ec: 00191913  slli         x18, x18, 1
    4f0: 00d90933  add          x18, x18, x13
    4f4: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4f8: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    4fc: 01490933  add          x18, x18, x20
    500: 04067993  andi         x19, x12, 64
    504: 00999993  slli         x19, x19, 9
    508: 0000aa37  lui          x20, 0x0000a  # x20 = 0x0000a000
    50c: 010a0a33  add          x20, x20, x16
    510: 00161a93  slli         x21, x12, 1
    514: 00037b37  lui          x22, 0x00037  # x22 = 0x00037000 · arc_apb_reset_unit + 0x7000
    518: 880b0b13  addi         x22, x22, -1920  # x22 = 0x00036880 · arc_apb_reset_unit + 0x6880
    51c: 016a8ab3  add          x21, x21, x22
    520: ffc10113  addi         x2, x2, -4
    524: 01412023  sw           x20, 0(x2)  # Address depends on runtime register values
    528: 00080f93  addi         x31, x16, 0
    52c: 00088f13  addi         x30, x17, 0
    530: 00090e93  addi         x29, x18, 0
    534: 00070e13  addi         x28, x14, 0
    538: 00098d93  addi         x27, x19, 0
    53c: 000a0d13  addi         x26, x20, 0
    540: 000a8c93  addi         x25, x21, 0
loc_544:
    544: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    548: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    54c: 01ba4a33  xor          x20, x20, x27
    550: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    554: 000d5a03  lhu          x20, 0(x26)  # Address depends on runtime register values
    558: 014c9023  sh           x20, 0(x25)  # Address depends on runtime register values
    55c: 002d0d13  addi         x26, x26, 2
    560: 002c8c93  addi         x25, x25, 2
    564: 002f8f93  addi         x31, x31, 2
    568: 002f0f13  addi         x30, x30, 2
    56c: 002e8e93  addi         x29, x29, 2
    570: fffe0e13  addi         x28, x28, -1
    574: fc0e18e3  bne          x28, x0, 0x00000544  # target 0x00000544
    578: 00012a03  lw           x20, 0(x2)  # Address depends on runtime register values
    57c: 00410113  addi         x2, x2, 4
    580: 00e60633  add          x12, x12, x14
    584: 00e585b3  add          x11, x11, x14
    588: 00a00793  addi         x15, x0, 10  # x15 = 0x0000000a
    58c: 04000993  addi         x19, x0, 64  # x19 = 0x00000040
    590: 01357463  bgeu         x10, x19, 0x00000598  # target 0x00000598
    594: 00178793  addi         x15, x15, 1  # x15 = 0x0000000b
loc_598:
    598: 00f59663  bne          x11, x15, 0x000005a4  # target 0x000005a4
    59c: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    5a0: 00150513  addi         x10, x10, 1
loc_5a4:
    5a4: 08000793  addi         x15, x0, 128  # x15 = 0x00000080
    5a8: eaf66ee3  bltu         x12, x15, 0x00000464  # target 0x00000464
    5ac: 000373b7  lui          x7, 0x00037  # x7 = 0x00037000 · arc_apb_reset_unit + 0x7000
    5b0: 08038393  addi         x7, x7, 128  # x7 = 0x00037080 · arc_apb_reset_unit + 0x7080
    5b4: 006383b3  add          x7, x7, x6
    5b8: 00038f93  addi         x31, x7, 0
    5bc: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    5c0: 880f0f13  addi         x30, x30, -1920  # x30 = 0x00020880
    5c4: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5c8: 01d000ef  jal          x1, 0x00000de4  # target 0x00000de4; x1 = 0x000005cc
    5cc: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    5d0: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00020880
    5d4: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    5d8: 980f0f13  addi         x30, x30, -1664  # x30 = 0x00020980
    5dc: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5e0: 059000ef  jal          x1, 0x00000e38  # target 0x00000e38; x1 = 0x000005e4
    5e4: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    5e8: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00020880
    5ec: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    5f0: a80f0f13  addi         x30, x30, -1408  # x30 = 0x00020a80
    5f4: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5f8: 041000ef  jal          x1, 0x00000e38  # target 0x00000e38; x1 = 0x000005fc
    5fc: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    600: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00020880
    604: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    608: b80f0f13  addi         x30, x30, -1152  # x30 = 0x00020b80
    60c: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    610: 029000ef  jal          x1, 0x00000e38  # target 0x00000e38; x1 = 0x00000614
    614: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    618: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00020880
    61c: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    620: c80f0f13  addi         x30, x30, -896  # x30 = 0x00020c80
    624: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    628: 011000ef  jal          x1, 0x00000e38  # target 0x00000e38; x1 = 0x0000062c
    62c: 000383b7  lui          x7, 0x00038  # x7 = 0x00038000 · arc_apb_reset_unit + 0x8000
    630: 88038393  addi         x7, x7, -1920  # x7 = 0x00037880 · arc_apb_reset_unit + 0x7880
    634: 006383b3  add          x7, x7, x6
    638: 00038f93  addi         x31, x7, 0
    63c: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    640: 080f0f13  addi         x30, x30, 128  # x30 = 0x00021080
    644: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    648: 79c000ef  jal          x1, 0x00000de4  # target 0x00000de4; x1 = 0x0000064c
    64c: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    650: 080f8f93  addi         x31, x31, 128  # x31 = 0x00021080
    654: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    658: 180f0f13  addi         x30, x30, 384  # x30 = 0x00021180
    65c: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    660: 7d8000ef  jal          x1, 0x00000e38  # target 0x00000e38; x1 = 0x00000664
    664: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    668: 080f8f93  addi         x31, x31, 128  # x31 = 0x00021080
    66c: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    670: 280f0f13  addi         x30, x30, 640  # x30 = 0x00021280
    674: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    678: 7c0000ef  jal          x1, 0x00000e38  # target 0x00000e38; x1 = 0x0000067c
    67c: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    680: 080f8f93  addi         x31, x31, 128  # x31 = 0x00021080
    684: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    688: 380f0f13  addi         x30, x30, 896  # x30 = 0x00021380
    68c: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    690: 7a8000ef  jal          x1, 0x00000e38  # target 0x00000e38; x1 = 0x00000694
    694: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    698: 080f8f93  addi         x31, x31, 128  # x31 = 0x00021080
    69c: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    6a0: 480f0f13  addi         x30, x30, 1152  # x30 = 0x00021480
    6a4: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    6a8: 790000ef  jal          x1, 0x00000e38  # target 0x00000e38; x1 = 0x000006ac
    6ac: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6b0: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    6b4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    6b8: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    6bc: 00520233  add          x4, x4, x5
    6c0: 00022337  lui          x6, 0x00022  # x6 = 0x00022000
    6c4: 88030313  addi         x6, x6, -1920  # x6 = 0x00021880
    6c8: 00626663  bltu         x4, x6, 0x000006d4  # target 0x000006d4
    6cc: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    6d0: 40720233  sub          x4, x4, x7
loc_6d4:
    6d4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6d8: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    6dc: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    6e0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    6e4: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    6e8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    6ec: 00420213  addi         x4, x4, 4
    6f0: 01021213  slli         x4, x4, 16
    6f4: 01025213  srli         x4, x4, 16
    6f8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    6fc: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    700: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    704: ffb4d2b7  lui          x5, 0xffb4d  # x5 = 0xffb4d000
    708: 02828293  addi         x5, x5, 40  # x5 = 0xffb4d028
    70c: 0042a023  sw           x4, 0(x5)  # 0xffb4d028; write runtime value
    710: 0ff0000f  fence        0xf, 0xf
    714: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    718: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
    71c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884
    720: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_724:
    724: ffb4f437  lui          x8, 0xffb4f  # x8 = 0xffb4f000
    728: 02840413  addi         x8, x8, 40  # x8 = 0xffb4f028
    72c: 00045283  lhu          x5, 0(x8)  # 0xffb4f028
    730: 40428333  sub          x6, x5, x4
    734: 01031313  slli         x6, x6, 16
    738: 01035313  srli         x6, x6, 16
    73c: 00737663  bgeu         x6, x7, 0x00000748  # target 0x00000748
    740: 0ff0000f  fence        0xf, 0xf
    744: fe1ff06f  jal          x0, 0x00000724  # target 0x00000724
loc_748:
    748: 0ff0000f  fence        0xf, 0xf
    74c: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
    750: 90438393  addi         x7, x7, -1788  # x7 = 0x0000e904
    754: 0003a203  lw           x4, 0(x7)  # param attention_core; 0x0000e904
    758: 00c00393  addi         x7, x0, 12  # x7 = 0x0000000c
    75c: 02725233  divu         x4, x4, x7
    760: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    764: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000790
    768: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
    76c: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    770: 00100313  addi         x6, x0, 1  # x6 = 0x00000001
    774: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    778: 00747a63  bgeu         x8, x7, 0x0000078c  # target 0x0000078c
    77c: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    780: 08000413  addi         x8, x0, 128  # x8 = 0x00000080
    784: 00747463  bgeu         x8, x7, 0x0000078c  # target 0x0000078c
    788: 00c00313  addi         x6, x0, 12  # x6 = 0x0000000c
loc_78c:
    78c: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    790: 90848493  addi         x9, x9, -1784  # x9 = 0x0000e908
    794: 0004a383  lw           x7, 0(x9)  # param attention_phase; 0x0000e908
    798: 79000593  addi         x11, x0, 1936  # x11 = 0x00000790
    79c: 0005a483  lw           x9, 0(x11)  # param kv_blocks; 0x00000790
    7a0: 00100413  addi         x8, x0, 1  # x8 = 0x00000001
    7a4: 00400513  addi         x10, x0, 4  # x10 = 0x00000004
    7a8: 00957a63  bgeu         x10, x9, 0x000007bc  # target 0x000007bc
    7ac: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    7b0: 08000513  addi         x10, x0, 128  # x10 = 0x00000080
    7b4: 00957463  bgeu         x10, x9, 0x000007bc  # target 0x000007bc
    7b8: 00c00413  addi         x8, x0, 12  # x8 = 0x0000000c
loc_7bc:
    7bc: 008282b3  add          x5, x5, x8
    7c0: fff28293  addi         x5, x5, -1
    7c4: 407282b3  sub          x5, x5, x7
    7c8: 0282d2b3  divu         x5, x5, x8
    7cc: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    7d0: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    7d4: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888
    7d8: 00002437  lui          x8, 0x00002  # x8 = 0x00002000
    7dc: 008383b3  add          x7, x7, x8
    7e0: 000114b7  lui          x9, 0x00011  # x9 = 0x00011000
    7e4: 08048493  addi         x9, x9, 128  # x9 = 0x00011080
    7e8: 0093e663  bltu         x7, x9, 0x000007f4  # target 0x000007f4
    7ec: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    7f0: 40a383b3  sub          x7, x7, x10
loc_7f4:
    7f4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    7f8: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    7fc: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
    800: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    804: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    808: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c
    80c: 00438393  addi         x7, x7, 4
    810: 01039393  slli         x7, x7, 16
    814: 0103d393  srli         x7, x7, 16
    818: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    81c: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    820: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c; write runtime value
    824: ffb48437  lui          x8, 0xffb48  # x8 = 0xffb48000
    828: 02840413  addi         x8, x8, 40  # x8 = 0xffb48028
    82c: 00742023  sw           x7, 0(x8)  # 0xffb48028; write runtime value
    830: 0ff0000f  fence        0xf, 0xf
    834: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    838: 00028413  addi         x8, x5, 0
loc_83c:
    83c: 3483f663  bgeu         x7, x8, 0x00000b88  # target 0x00000b88
    840: 00025493  srli         x9, x4, 0
    844: 00a49493  slli         x9, x9, 10
    848: 02638533  mul          x10, x7, x6
    84c: 0000f637  lui          x12, 0x0000f  # x12 = 0x0000f000
    850: 90860613  addi         x12, x12, -1784  # x12 = 0x0000e908
    854: 00062583  lw           x11, 0(x12)  # param attention_phase; 0x0000e908
    858: 00b50533  add          x10, x10, x11
    85c: 00251513  slli         x10, x10, 2
    860: 00a484b3  add          x9, x9, x10
    864: 328000ef  jal          x1, 0x00000b8c  # target 0x00000b8c; x1 = 0x00000868
    868: 340000ef  jal          x1, 0x00000ba8  # target 0x00000ba8; x1 = 0x0000086c
    86c: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    870: 89480813  addi         x16, x16, -1900  # x16 = 0xffb00894 · riscv_local_mem + 0x894
    874: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x894 · 0xffb00894
loc_878:
    878: ffb49837  lui          x16, 0xffb49  # x16 = 0xffb49000
    87c: 02080813  addi         x16, x16, 32  # x16 = 0xffb49020
    880: 00085603  lhu          x12, 0(x16)  # 0xffb49020
    884: 40c586b3  sub          x13, x11, x12
    888: 01069693  slli         x13, x13, 16
    88c: 0106d693  srli         x13, x13, 16
    890: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    894: 40d70733  sub          x14, x14, x13
    898: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    89c: 00f77663  bgeu         x14, x15, 0x000008a8  # target 0x000008a8
    8a0: 0ff0000f  fence        0xf, 0xf
    8a4: fd5ff06f  jal          x0, 0x00000878  # target 0x00000878
loc_8a8:
    8a8: 0ff0000f  fence        0xf, 0xf
    8ac: 00048593  addi         x11, x9, 0
    8b0: 00058f93  addi         x31, x11, 0
    8b4: 5a0000ef  jal          x1, 0x00000e54  # target 0x00000e54; x1 = 0x000008b8
    8b8: 000a8613  addi         x12, x21, 0
    8bc: 000b0693  addi         x13, x22, 0
    8c0: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    8c4: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    8c8: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    8cc: 00060f93  addi         x31, x12, 0
    8d0: 00068f13  addi         x30, x13, 0
    8d4: 00070e93  addi         x29, x14, 0
    8d8: 338000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x000008dc
    8dc: 00148593  addi         x11, x9, 1
    8e0: 00058f93  addi         x31, x11, 0
    8e4: 570000ef  jal          x1, 0x00000e54  # target 0x00000e54; x1 = 0x000008e8
    8e8: 000a8613  addi         x12, x21, 0
    8ec: 000b0693  addi         x13, x22, 0
    8f0: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    8f4: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    8f8: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    8fc: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    900: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    904: 00f70733  add          x14, x14, x15
    908: 00060f93  addi         x31, x12, 0
    90c: 00068f13  addi         x30, x13, 0
    910: 00070e93  addi         x29, x14, 0
    914: 2fc000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x00000918
    918: 00248593  addi         x11, x9, 2
    91c: 00058f93  addi         x31, x11, 0
    920: 534000ef  jal          x1, 0x00000e54  # target 0x00000e54; x1 = 0x00000924
    924: 000a8613  addi         x12, x21, 0
    928: 000b0693  addi         x13, x22, 0
    92c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    930: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    934: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    938: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    93c: 00f70733  add          x14, x14, x15
    940: 00060f93  addi         x31, x12, 0
    944: 00068f13  addi         x30, x13, 0
    948: 00070e93  addi         x29, x14, 0
    94c: 2c4000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x00000950
    950: 00348593  addi         x11, x9, 3
    954: 00058f93  addi         x31, x11, 0
    958: 4fc000ef  jal          x1, 0x00000e54  # target 0x00000e54; x1 = 0x0000095c
    95c: 000a8613  addi         x12, x21, 0
    960: 000b0693  addi         x13, x22, 0
    964: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    968: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    96c: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    970: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    974: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    978: 00f70733  add          x14, x14, x15
    97c: 00060f93  addi         x31, x12, 0
    980: 00068f13  addi         x30, x13, 0
    984: 00070e93  addi         x29, x14, 0
    988: 288000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x0000098c
    98c: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    990: 89c80813  addi         x16, x16, -1892  # x16 = 0xffb0089c · riscv_local_mem + 0x89c
    994: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x89c · 0xffb0089c
loc_998:
    998: ffb4a837  lui          x16, 0xffb4a  # x16 = 0xffb4a000
    99c: 02080813  addi         x16, x16, 32  # x16 = 0xffb4a020
    9a0: 00085603  lhu          x12, 0(x16)  # 0xffb4a020
    9a4: 40c586b3  sub          x13, x11, x12
    9a8: 01069693  slli         x13, x13, 16
    9ac: 0106d693  srli         x13, x13, 16
    9b0: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    9b4: 40d70733  sub          x14, x14, x13
    9b8: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    9bc: 00f77663  bgeu         x14, x15, 0x000009c8  # target 0x000009c8
    9c0: 0ff0000f  fence        0xf, 0xf
    9c4: fd5ff06f  jal          x0, 0x00000998  # target 0x00000998
loc_9c8:
    9c8: 0ff0000f  fence        0xf, 0xf
    9cc: 00048593  addi         x11, x9, 0
    9d0: 00058f93  addi         x31, x11, 0
    9d4: 4cc000ef  jal          x1, 0x00000ea0  # target 0x00000ea0; x1 = 0x000009d8
    9d8: 000a8613  addi         x12, x21, 0
    9dc: 000b0693  addi         x13, x22, 0
    9e0: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    9e4: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    9e8: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    9ec: 00060f93  addi         x31, x12, 0
    9f0: 00068f13  addi         x30, x13, 0
    9f4: 00070e93  addi         x29, x14, 0
    9f8: 218000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x000009fc
    9fc: 00148593  addi         x11, x9, 1
    a00: 00058f93  addi         x31, x11, 0
    a04: 49c000ef  jal          x1, 0x00000ea0  # target 0x00000ea0; x1 = 0x00000a08
    a08: 000a8613  addi         x12, x21, 0
    a0c: 000b0693  addi         x13, x22, 0
    a10: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a14: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    a18: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    a1c: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a20: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    a24: 00f70733  add          x14, x14, x15
    a28: 00060f93  addi         x31, x12, 0
    a2c: 00068f13  addi         x30, x13, 0
    a30: 00070e93  addi         x29, x14, 0
    a34: 1dc000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x00000a38
    a38: 00248593  addi         x11, x9, 2
    a3c: 00058f93  addi         x31, x11, 0
    a40: 460000ef  jal          x1, 0x00000ea0  # target 0x00000ea0; x1 = 0x00000a44
    a44: 000a8613  addi         x12, x21, 0
    a48: 000b0693  addi         x13, x22, 0
    a4c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a50: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    a54: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    a58: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a5c: 00f70733  add          x14, x14, x15
    a60: 00060f93  addi         x31, x12, 0
    a64: 00068f13  addi         x30, x13, 0
    a68: 00070e93  addi         x29, x14, 0
    a6c: 1a4000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x00000a70
    a70: 00348593  addi         x11, x9, 3
    a74: 00058f93  addi         x31, x11, 0
    a78: 428000ef  jal          x1, 0x00000ea0  # target 0x00000ea0; x1 = 0x00000a7c
    a7c: 000a8613  addi         x12, x21, 0
    a80: 000b0693  addi         x13, x22, 0
    a84: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a88: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    a8c: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    a90: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    a94: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    a98: 00f70733  add          x14, x14, x15
    a9c: 00060f93  addi         x31, x12, 0
    aa0: 00068f13  addi         x30, x13, 0
    aa4: 00070e93  addi         x29, x14, 0
    aa8: 168000ef  jal          x1, 0x00000c10  # target 0x00000c10; x1 = 0x00000aac
    aac: 0fc000ef  jal          x1, 0x00000ba8  # target 0x00000ba8; x1 = 0x00000ab0
    ab0: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    ab4: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    ab8: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    abc: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    ac0: 00c585b3  add          x11, x11, x12
    ac4: 000156b7  lui          x13, 0x00015  # x13 = 0x00015000
    ac8: 08068693  addi         x13, x13, 128  # x13 = 0x00015080
    acc: 00d5e663  bltu         x11, x13, 0x00000ad8  # target 0x00000ad8
    ad0: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    ad4: 40e585b3  sub          x11, x11, x14
loc_ad8:
    ad8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    adc: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    ae0: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890; write runtime value
    ae4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    ae8: 89460613  addi         x12, x12, -1900  # x12 = 0xffb00894 · riscv_local_mem + 0x894
    aec: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x894 · 0xffb00894
    af0: 00458593  addi         x11, x11, 4
    af4: 01059593  slli         x11, x11, 16
    af8: 0105d593  srli         x11, x11, 16
    afc: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b00: 89460613  addi         x12, x12, -1900  # x12 = 0xffb00894 · riscv_local_mem + 0x894
    b04: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x894 · 0xffb00894; write runtime value
    b08: ffb49637  lui          x12, 0xffb49  # x12 = 0xffb49000
    b0c: 02860613  addi         x12, x12, 40  # x12 = 0xffb49028
    b10: 00b62023  sw           x11, 0(x12)  # 0xffb49028; write runtime value
    b14: 0ff0000f  fence        0xf, 0xf
    b18: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b1c: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    b20: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    b24: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    b28: 00c585b3  add          x11, x11, x12
    b2c: 000196b7  lui          x13, 0x00019  # x13 = 0x00019000
    b30: 08068693  addi         x13, x13, 128  # x13 = 0x00019080
    b34: 00d5e663  bltu         x11, x13, 0x00000b40  # target 0x00000b40
    b38: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    b3c: 40e585b3  sub          x11, x11, x14
loc_b40:
    b40: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b44: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    b48: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898; write runtime value
    b4c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b50: 89c60613  addi         x12, x12, -1892  # x12 = 0xffb0089c · riscv_local_mem + 0x89c
    b54: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x89c · 0xffb0089c
    b58: 00458593  addi         x11, x11, 4
    b5c: 01059593  slli         x11, x11, 16
    b60: 0105d593  srli         x11, x11, 16
    b64: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b68: 89c60613  addi         x12, x12, -1892  # x12 = 0xffb0089c · riscv_local_mem + 0x89c
    b6c: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x89c · 0xffb0089c; write runtime value
    b70: ffb4a637  lui          x12, 0xffb4a  # x12 = 0xffb4a000
    b74: 02860613  addi         x12, x12, 40  # x12 = 0xffb4a028
    b78: 00b62023  sw           x11, 0(x12)  # 0xffb4a028; write runtime value
    b7c: 0ff0000f  fence        0xf, 0xf
    b80: 00138393  addi         x7, x7, 1
    b84: cb9ff06f  jal          x0, 0x0000083c  # target 0x0000083c
loc_b88:
    b88: 3640006f  jal          x0, 0x00000eec  # target 0x00000eec
loc_b8c:
    b8c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    b90: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    b94: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    b98: 000a0463  beq          x20, x0, 0x00000ba0  # target 0x00000ba0
    b9c: ff1ff06f  jal          x0, 0x00000b8c  # target 0x00000b8c
loc_ba0:
    ba0: 0ff0000f  fence        0xf, 0xf
    ba4: 00008067  jalr         x0, 0(x1)
loc_ba8:
    ba8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    bac: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    bb0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    bb4: 000a0463  beq          x20, x0, 0x00000bbc  # target 0x00000bbc
    bb8: ff1ff06f  jal          x0, 0x00000ba8  # target 0x00000ba8
loc_bbc:
    bbc: 0ff0000f  fence        0xf, 0xf
    bc0: 00008067  jalr         x0, 0(x1)
loc_bc4:
    bc4: 7a400a93  addi         x21, x0, 1956  # x21 = 0x000007a4
    bc8: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_cos; 0x000007a4
    bcc: 007a7d13  andi         x26, x20, 7
    bd0: ff8a7a13  andi         x20, x20, -8
    bd4: 01af8ab3  add          x21, x31, x26
    bd8: 007afb93  andi         x23, x21, 7
    bdc: 003ada93  srli         x21, x21, 3
    be0: 00ba9a93  slli         x21, x21, 11
    be4: 014a8ab3  add          x21, x21, x20
    be8: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000be8
    bec: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000c00
    bf0: 001b9b93  slli         x23, x23, 1
    bf4: 017b0b33  add          x22, x22, x23
    bf8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    bfc: 00008067  jalr         x0, 0(x1)
    c00: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    c04: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    c08: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    c0c: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_c10:
    c10: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c14: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    c18: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    c1c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    c20: 015a6463  bltu         x20, x21, 0x00000c28  # target 0x00000c28
    c24: fedff06f  jal          x0, 0x00000c10  # target 0x00000c10
loc_c28:
    c28: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c2c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    c30: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    c34: 014a1a13  slli         x20, x20, 20
    c38: 014a5a13  srli         x20, x20, 20
    c3c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_c40:
    c40: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    c44: 000b0463  beq          x22, x0, 0x00000c4c  # target 0x00000c4c
    c48: ff9ff06f  jal          x0, 0x00000c40  # target 0x00000c40
loc_c4c:
    c4c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    c50: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    c54: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    c58: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    c5c: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    c60: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    c64: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    c68: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    c6c: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    c70: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    c74: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    c78: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    c7c: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    c80: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    c84: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    c88: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    c8c: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    c90: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    c94: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    c98: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    c9c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    ca0: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_ca4:
    ca4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    ca8: 000b0463  beq          x22, x0, 0x00000cb0  # target 0x00000cb0
    cac: ff9ff06f  jal          x0, 0x00000ca4  # target 0x00000ca4
loc_cb0:
    cb0: 00008067  jalr         x0, 0(x1)
loc_cb4:
    cb4: 7a800a93  addi         x21, x0, 1960  # x21 = 0x000007a8
    cb8: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_sin; 0x000007a8
    cbc: 007a7d13  andi         x26, x20, 7
    cc0: ff8a7a13  andi         x20, x20, -8
    cc4: 01af8ab3  add          x21, x31, x26
    cc8: 007afb93  andi         x23, x21, 7
    ccc: 003ada93  srli         x21, x21, 3
    cd0: 00ba9a93  slli         x21, x21, 11
    cd4: 014a8ab3  add          x21, x21, x20
    cd8: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000cd8
    cdc: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000cf0
    ce0: 001b9b93  slli         x23, x23, 1
    ce4: 017b0b33  add          x22, x22, x23
    ce8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    cec: 00008067  jalr         x0, 0(x1)
    cf0: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    cf4: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    cf8: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    cfc: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d00:
    d00: 79800a93  addi         x21, x0, 1944  # x21 = 0x00000798
    d04: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_q_compact; 0x00000798
    d08: 007a7d13  andi         x26, x20, 7
    d0c: ff8a7a13  andi         x20, x20, -8
    d10: 01af8ab3  add          x21, x31, x26
    d14: 007afb93  andi         x23, x21, 7
    d18: 003ada93  srli         x21, x21, 3
    d1c: 00ba9a93  slli         x21, x21, 11
    d20: 014a8ab3  add          x21, x21, x20
    d24: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d24
    d28: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d3c
    d2c: 001b9b93  slli         x23, x23, 1
    d30: 017b0b33  add          x22, x22, x23
    d34: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d38: 00008067  jalr         x0, 0(x1)
    d3c: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    d40: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d44: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    d48: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d4c:
    d4c: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    d50: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_k_compact; 0x0000079c
    d54: 007a7d13  andi         x26, x20, 7
    d58: ff8a7a13  andi         x20, x20, -8
    d5c: 01af8ab3  add          x21, x31, x26
    d60: 007afb93  andi         x23, x21, 7
    d64: 003ada93  srli         x21, x21, 3
    d68: 00ba9a93  slli         x21, x21, 11
    d6c: 014a8ab3  add          x21, x21, x20
    d70: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d70
    d74: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d88
    d78: 001b9b93  slli         x23, x23, 1
    d7c: 017b0b33  add          x22, x22, x23
    d80: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d84: 00008067  jalr         x0, 0(x1)
    d88: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    d8c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d90: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    d94: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d98:
    d98: 7a000a93  addi         x21, x0, 1952  # x21 = 0x000007a0
    d9c: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_v_compact; 0x000007a0
    da0: 007a7d13  andi         x26, x20, 7
    da4: ff8a7a13  andi         x20, x20, -8
    da8: 01af8ab3  add          x21, x31, x26
    dac: 007afb93  andi         x23, x21, 7
    db0: 003ada93  srli         x21, x21, 3
    db4: 00ba9a93  slli         x21, x21, 11
    db8: 014a8ab3  add          x21, x21, x20
    dbc: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000dbc
    dc0: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000dd4
    dc4: 001b9b93  slli         x23, x23, 1
    dc8: 017b0b33  add          x22, x22, x23
    dcc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    dd0: 00008067  jalr         x0, 0(x1)
    dd4: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    dd8: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    ddc: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    de0: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_de4:
    de4: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    de8: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    dec: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    df0: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    df4: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    df8: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    dfc: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    e00: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    e04: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    e08: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    e0c: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    e10: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    e14: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    e18: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    e1c: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    e20: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    e24: 020f8f93  addi         x31, x31, 32
    e28: 020f0f13  addi         x30, x30, 32
    e2c: ff8e8e93  addi         x29, x29, -8
    e30: fa0e9ae3  bne          x29, x0, 0x00000de4  # target 0x00000de4
    e34: 00008067  jalr         x0, 0(x1)
loc_e38:
    e38: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    e3c: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    e40: 004f8f93  addi         x31, x31, 4
    e44: 004f0f13  addi         x30, x30, 4
    e48: fffe8e93  addi         x29, x29, -1
    e4c: fe0e96e3  bne          x29, x0, 0x00000e38  # target 0x00000e38
    e50: 00008067  jalr         x0, 0(x1)
loc_e54:
    e54: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    e58: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    e5c: 007a7d13  andi         x26, x20, 7
    e60: ff8a7a13  andi         x20, x20, -8
    e64: 01af8ab3  add          x21, x31, x26
    e68: 007afb93  andi         x23, x21, 7
    e6c: 003ada93  srli         x21, x21, 3
    e70: 00ba9a93  slli         x21, x21, 11
    e74: 014a8ab3  add          x21, x21, x20
    e78: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e78
    e7c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e90
    e80: 001b9b93  slli         x23, x23, 1
    e84: 017b0b33  add          x22, x22, x23
    e88: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e8c: 00008067  jalr         x0, 0(x1)
    e90: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    e94: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e98: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    e9c: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_ea0:
    ea0: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    ea4: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    ea8: 007a7d13  andi         x26, x20, 7
    eac: ff8a7a13  andi         x20, x20, -8
    eb0: 01af8ab3  add          x21, x31, x26
    eb4: 007afb93  andi         x23, x21, 7
    eb8: 003ada93  srli         x21, x21, 3
    ebc: 00ba9a93  slli         x21, x21, 11
    ec0: 014a8ab3  add          x21, x21, x20
    ec4: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000ec4
    ec8: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000edc
    ecc: 001b9b93  slli         x23, x23, 1
    ed0: 017b0b33  add          x22, x22, x23
    ed4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    ed8: 00008067  jalr         x0, 0(x1)
    edc: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    ee0: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    ee4: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    ee8: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    eec:           j FW_BRISC+4   # return to firmware, linked at install
